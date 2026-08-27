from __future__ import annotations

import math
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from ..track_identity import identify_track
from .backend import RetrievalBackend
from .catalog import CatalogTrack, filter_track_ids, load_catalog_tracks
from .contracts import EmbeddingIdentity, EmbeddingVector, SearchFilter, SearchHit
from .index import DenseCosineIndex
from .segment_store import RepresentativeRecord, SegmentMetadataStore
from .service import CatalogSearchHit
from .storage import RetrievalStore, StoredEmbedding

SEGMENT_POLICY_VERSION = "fixed30-hop30-cap64-min1-v1"
ProgressCallback = Callable[[int, int, str], None]


@dataclass(frozen=True)
class SegmentPolicy:
    window_s: float = 30.0
    hop_s: float = 30.0
    min_segment_s: float = 1.0
    max_segments: int = 64
    version: str = SEGMENT_POLICY_VERSION

    def __post_init__(self) -> None:
        if self.window_s <= 0 or self.hop_s <= 0 or self.min_segment_s <= 0:
            raise ValueError("segment durations must be positive")
        if self.min_segment_s > self.window_s:
            raise ValueError("min_segment_s must be <= window_s")
        if self.max_segments <= 0:
            raise ValueError("max_segments must be positive")
        if not self.version.strip():
            raise ValueError("segment policy version must not be empty")


@dataclass(frozen=True)
class SegmentWindow:
    index: int
    start_s: float
    end_s: float
    short_window: bool

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s


@dataclass(frozen=True)
class RepresentativeSelection:
    segment: StoredEmbedding
    score: float


@dataclass(frozen=True)
class SegmentIndexReport:
    backend_fingerprint: str
    policy_version: str
    selected_tracks: int
    available_tracks: int
    missing_paths: int
    too_short_tracks: int
    planned_segments: int
    segment_cache_hits: int
    segment_cache_misses: int
    embedded_segments: int
    representative_updates: int
    source_failures: int
    embedding_failures: int
    failed_track_ids: tuple[str, ...]
    elapsed_seconds: float
    vector_payload_bytes: int
    retrieval_db_bytes: int

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["failed_track_ids"] = list(self.failed_track_ids)
        return payload


@dataclass(frozen=True)
class SegmentStatus:
    backend_fingerprint: str
    policy_version: str
    segment_extension_schema: int
    catalog_tracks: int
    segment_embeddings: int
    representative_embeddings: int
    represented_tracks: int
    stale_segment_embeddings: int
    stale_representative_embeddings: int
    retrieval_db_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SegmentSearchResult:
    query_scope: str
    target_scope: str
    backend_fingerprint: str
    query_track_id: str
    start_s: float
    end_s: float
    top_k: int
    embedding_seconds: float
    ranking_seconds: float
    cache_hit: bool
    filters: SearchFilter
    hits: tuple[CatalogSearchHit, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_scope": self.query_scope,
            "target_scope": self.target_scope,
            "backend_fingerprint": self.backend_fingerprint,
            "query_track_id": self.query_track_id,
            "start_s": self.start_s,
            "end_s": self.end_s,
            "top_k": self.top_k,
            "embedding_seconds": self.embedding_seconds,
            "ranking_seconds": self.ranking_seconds,
            "cache_hit": self.cache_hit,
            "filters": asdict(self.filters),
            "hits": [asdict(hit) for hit in self.hits],
        }


def plan_segments(duration_s: float, policy: SegmentPolicy = SegmentPolicy()) -> tuple[SegmentWindow, ...]:
    """Return deterministic retrieval windows for one source duration.

    Tails shorter than the backend's documented one-second final-window minimum are
    dropped rather than padded. Files shorter than that minimum return no windows.
    """

    if not math.isfinite(duration_s) or duration_s <= 0:
        raise ValueError("duration_s must be positive and finite")
    if duration_s < policy.min_segment_s:
        return ()

    windows: list[SegmentWindow] = []
    start_s = 0.0
    while start_s < duration_s:
        end_s = min(start_s + policy.window_s, duration_s)
        if end_s - start_s >= policy.min_segment_s:
            windows.append(
                SegmentWindow(
                    index=len(windows),
                    start_s=round(start_s, 6),
                    end_s=round(end_s, 6),
                    short_window=(end_s - start_s) < policy.window_s,
                )
            )
        start_s += policy.hop_s

    if len(windows) <= policy.max_segments:
        return tuple(windows)
    if policy.max_segments == 1:
        chosen = [windows[len(windows) // 2]]
    else:
        positions = [
            round(i * (len(windows) - 1) / (policy.max_segments - 1))
            for i in range(policy.max_segments)
        ]
        chosen = [windows[position] for position in positions]
    return tuple(
        SegmentWindow(
            index=index,
            start_s=window.start_s,
            end_s=window.end_s,
            short_window=window.short_window,
        )
        for index, window in enumerate(chosen)
    )


def select_representative(records: Sequence[StoredEmbedding]) -> RepresentativeSelection:
    if not records:
        raise ValueError("at least one segment embedding is required")
    valid: list[StoredEmbedding] = []
    dimension: int | None = None
    for record in records:
        identity = record.identity
        if identity.scope != "segment" or identity.start_s is None or identity.end_s is None:
            raise ValueError("representative selection requires segment embeddings")
        if dimension is None:
            dimension = record.vector.dimension
        elif record.vector.dimension != dimension:
            raise ValueError("mixed segment embedding dimensions")
        valid.append(record)

    matrix = np.asarray([record.vector.values for record in valid], dtype=np.float64)
    centroid = matrix.mean(axis=0)
    norm = float(np.linalg.norm(centroid))
    if not math.isfinite(norm) or norm <= 0:
        raise ValueError("segment centroid has zero or invalid norm")
    centroid /= norm
    scores = matrix @ centroid
    candidates = sorted(
        range(len(valid)),
        key=lambda index: (
            -float(scores[index]),
            float(valid[index].identity.start_s or 0.0),
            float(valid[index].identity.end_s or 0.0),
            valid[index].cache_key,
        ),
    )
    winner = candidates[0]
    return RepresentativeSelection(segment=valid[winner], score=float(scores[winner]))


def _duration_seconds(path: Path) -> float:
    info = sf.info(str(path))
    duration = float(info.duration)
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError(f"invalid audio duration: {duration}")
    return duration


def _segment_identity(
    backend: RetrievalBackend,
    track_id: str,
    window: SegmentWindow,
    *,
    scope: str = "segment",
) -> EmbeddingIdentity:
    return EmbeddingIdentity(
        backend_fingerprint=backend.info.fingerprint,
        scope=scope,  # type: ignore[arg-type]
        track_id=track_id,
        start_s=window.start_s,
        end_s=window.end_s,
    )


def _select_tracks(
    tracks: list[CatalogTrack],
    *,
    limit: int | None,
    track_ids: Sequence[str] | None,
) -> list[CatalogTrack]:
    selected = tracks
    if track_ids is not None:
        wanted = set(track_ids)
        selected = [track for track in selected if track.track_id in wanted]
    if limit is not None:
        if limit <= 0:
            raise ValueError("limit must be positive")
        selected = selected[:limit]
    return selected


def index_segments(
    *,
    store: RetrievalStore,
    history_path: Path,
    backend: RetrievalBackend,
    policy: SegmentPolicy = SegmentPolicy(),
    limit: int | None = None,
    track_ids: Sequence[str] | None = None,
    progress: ProgressCallback | None = None,
) -> SegmentIndexReport:
    started = time.perf_counter()
    metadata_store = SegmentMetadataStore(store)
    tracks = _select_tracks(
        load_catalog_tracks(history_path),
        limit=limit,
        track_ids=track_ids,
    )
    store.register_backend(backend.info)

    available_tracks = 0
    missing_paths = 0
    too_short_tracks = 0
    planned_segments = 0
    cache_hits = 0
    cache_misses = 0
    embedded_segments = 0
    representative_updates = 0
    source_failures = 0
    embedding_failures = 0
    failed_track_ids: list[str] = []

    total = len(tracks)
    for current, track in enumerate(tracks, 1):
        if progress is not None:
            progress(current, total, track.path or track.track_id)
        if not track.path_exists or track.path is None:
            missing_paths += 1
            continue
        available_tracks += 1
        source_path = Path(track.path)
        try:
            windows = plan_segments(_duration_seconds(source_path), policy)
        except (OSError, RuntimeError, ValueError, sf.LibsndfileError):
            source_failures += 1
            failed_track_ids.append(track.track_id)
            continue
        if not windows:
            too_short_tracks += 1
            continue
        planned_segments += len(windows)

        stored_segments: list[StoredEmbedding] = []
        track_failed = False
        for window in windows:
            identity = _segment_identity(backend, track.track_id, window)
            try:
                stored = store.get(identity)
            except ValueError:
                store.delete_identity(identity)
                stored = None
            if stored is not None:
                cache_hits += 1
                if stored.path != track.path:
                    store.update_path(identity, track.path)
                    refreshed = store.get(identity)
                    if refreshed is not None:
                        stored = refreshed
                stored_segments.append(stored)
                continue

            cache_misses += 1
            try:
                vector = backend.embed_audio(
                    source_path,
                    track_id=track.track_id,
                    start_s=window.start_s,
                    end_s=window.end_s,
                )
                if vector.identity != identity:
                    raise ValueError("backend returned unexpected segment embedding identity")
                store.put(vector, backend=backend.info, path=track.path)
                stored = store.get(identity)
                if stored is None:
                    raise RuntimeError("stored segment embedding could not be reloaded")
                stored_segments.append(stored)
                embedded_segments += 1
            except (OSError, RuntimeError, ValueError):
                embedding_failures += 1
                track_failed = True

        if not stored_segments:
            if track_failed:
                failed_track_ids.append(track.track_id)
            continue
        try:
            selection = select_representative(stored_segments)
            chosen = selection.segment
            assert chosen.identity.start_s is not None
            assert chosen.identity.end_s is not None
            representative_identity = EmbeddingIdentity(
                backend_fingerprint=backend.info.fingerprint,
                scope="representative",
                track_id=track.track_id,
                start_s=chosen.identity.start_s,
                end_s=chosen.identity.end_s,
            )
            representative_vector = EmbeddingVector(
                identity=representative_identity,
                values=chosen.vector.values,
            )
            store.put(representative_vector, backend=backend.info, path=track.path)
            metadata_store.replace_representative(
                backend_fingerprint=backend.info.fingerprint,
                track_id=track.track_id,
                policy_version=policy.version,
                start_s=representative_identity.start_s,
                end_s=representative_identity.end_s,
                score=selection.score,
                segment_cache_key=chosen.cache_key,
                representative_cache_key=representative_identity.cache_key,
            )
            representative_updates += 1
        except (RuntimeError, ValueError):
            embedding_failures += 1
            track_failed = True

        if track_failed and track.track_id not in failed_track_ids:
            failed_track_ids.append(track.track_id)

    current_segment_count = store.stats(
        backend_fingerprint=backend.info.fingerprint
    ).get("segment", 0)
    return SegmentIndexReport(
        backend_fingerprint=backend.info.fingerprint,
        policy_version=policy.version,
        selected_tracks=total,
        available_tracks=available_tracks,
        missing_paths=missing_paths,
        too_short_tracks=too_short_tracks,
        planned_segments=planned_segments,
        segment_cache_hits=cache_hits,
        segment_cache_misses=cache_misses,
        embedded_segments=embedded_segments,
        representative_updates=representative_updates,
        source_failures=source_failures,
        embedding_failures=embedding_failures,
        failed_track_ids=tuple(sorted(set(failed_track_ids))),
        elapsed_seconds=time.perf_counter() - started,
        vector_payload_bytes=current_segment_count * backend.info.embedding_dim * 4,
        retrieval_db_bytes=store.path.stat().st_size if store.path.exists() else 0,
    )


def segment_status(
    *,
    store: RetrievalStore,
    history_path: Path,
    backend_fingerprint: str,
    policy: SegmentPolicy = SegmentPolicy(),
) -> SegmentStatus:
    metadata_store = SegmentMetadataStore(store)
    stats = store.stats(backend_fingerprint=backend_fingerprint)
    return SegmentStatus(
        backend_fingerprint=backend_fingerprint,
        policy_version=policy.version,
        segment_extension_schema=metadata_store.schema_version(),
        catalog_tracks=len(load_catalog_tracks(history_path)),
        segment_embeddings=stats.get("segment", 0),
        representative_embeddings=stats.get("representative", 0),
        represented_tracks=len(
            metadata_store.list_representatives(
                backend_fingerprint=backend_fingerprint,
                policy_version=policy.version,
            )
        ),
        stale_segment_embeddings=store.count_stale(
            active_backend_fingerprint=backend_fingerprint,
            scope="segment",
        ),
        stale_representative_embeddings=store.count_stale(
            active_backend_fingerprint=backend_fingerprint,
            scope="representative",
        ),
        retrieval_db_bytes=store.path.stat().st_size if store.path.exists() else 0,
    )


def _dense_index_for_scope(
    store: RetrievalStore,
    *,
    backend_fingerprint: str,
    scope: str,
) -> DenseCosineIndex:
    records = store.iter_audio(backend_fingerprint=backend_fingerprint, scope=scope)
    if not records:
        raise ValueError(f"no {scope} embeddings available for backend")
    return DenseCosineIndex(
        backend_fingerprint=backend_fingerprint,
        track_ids=tuple(str(record.identity.track_id) for record in records),
        paths=tuple(str(record.path) for record in records),
        matrix=np.asarray([record.vector.values for record in records], dtype=np.float32),
    )


def _enrich_hits(
    hits: list[SearchHit],
    tracks: list[CatalogTrack],
) -> tuple[CatalogSearchHit, ...]:
    metadata = {track.track_id: track for track in tracks}
    enriched: list[CatalogSearchHit] = []
    for hit in hits:
        track = metadata.get(hit.track_id)
        enriched.append(
            CatalogSearchHit(
                rank=hit.rank,
                track_id=hit.track_id,
                path=hit.path,
                similarity=hit.similarity,
                backend_fingerprint=hit.backend_fingerprint,
                family=track.family if track else None,
                genre=track.genre if track else None,
                confidence=track.confidence if track else None,
                bpm=track.bpm if track else None,
                key=track.key if track else None,
                vocal=track.vocal if track else None,
                moods=track.moods if track else (),
                instruments=track.instruments if track else (),
                production=track.production if track else (),
            )
        )
    return tuple(enriched)


def _rank_segment_query(
    *,
    store: RetrievalStore,
    history_path: Path,
    backend: RetrievalBackend,
    query_vector: EmbeddingVector,
    filters: SearchFilter,
    top_k: int,
    target_scope: str,
    exclude_track_id: str | None,
) -> tuple[tuple[CatalogSearchHit, ...], float]:
    if target_scope not in {"full", "representative"}:
        raise ValueError("target_scope must be full or representative")
    tracks = load_catalog_tracks(history_path)
    allowed = filter_track_ids(tracks, filters)
    index = _dense_index_for_scope(
        store,
        backend_fingerprint=backend.info.fingerprint,
        scope=target_scope,
    )
    started = time.perf_counter()
    raw = index.search(
        query_vector,
        top_k=top_k,
        exclude_track_id=exclude_track_id,
        allowed_track_ids=allowed,
    )
    return _enrich_hits(raw, tracks), time.perf_counter() - started


def search_custom_interval(
    *,
    store: RetrievalStore,
    history_path: Path,
    backend: RetrievalBackend,
    audio_path: Path,
    start_s: float,
    end_s: float,
    target_scope: str = "full",
    top_k: int = 20,
    filters: SearchFilter | None = None,
    exclude_self: bool = True,
) -> SegmentSearchResult:
    if start_s < 0 or end_s <= start_s:
        raise ValueError("custom interval must satisfy 0 <= start_s < end_s")
    if end_s - start_s < 1.0:
        raise ValueError("custom interval must be at least 1 second")
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    selected_filters = filters or SearchFilter()
    identity = identify_track(Path(audio_path))
    window = SegmentWindow(index=0, start_s=start_s, end_s=end_s, short_window=False)
    query_identity = _segment_identity(backend, identity.track_id, window)

    started = time.perf_counter()
    cached = store.get(query_identity)
    cache_hit = cached is not None
    if cached is None:
        vector = backend.embed_audio(
            Path(audio_path),
            track_id=identity.track_id,
            start_s=start_s,
            end_s=end_s,
        )
        if vector.identity != query_identity:
            raise ValueError("backend returned unexpected custom-interval identity")
        store.put(vector, backend=backend.info, path=str(Path(audio_path).resolve()))
    else:
        vector = cached.vector
    embedding_seconds = time.perf_counter() - started

    hits, ranking_seconds = _rank_segment_query(
        store=store,
        history_path=history_path,
        backend=backend,
        query_vector=vector,
        filters=selected_filters,
        top_k=top_k,
        target_scope=target_scope,
        exclude_track_id=identity.track_id if exclude_self else None,
    )
    return SegmentSearchResult(
        query_scope="custom",
        target_scope=target_scope,
        backend_fingerprint=backend.info.fingerprint,
        query_track_id=identity.track_id,
        start_s=start_s,
        end_s=end_s,
        top_k=top_k,
        embedding_seconds=embedding_seconds,
        ranking_seconds=ranking_seconds,
        cache_hit=cache_hit,
        filters=selected_filters,
        hits=hits,
    )


def search_representative_track(
    *,
    store: RetrievalStore,
    history_path: Path,
    backend: RetrievalBackend,
    track_id: str,
    target_scope: str = "full",
    top_k: int = 20,
    filters: SearchFilter | None = None,
    exclude_self: bool = True,
    policy: SegmentPolicy = SegmentPolicy(),
) -> SegmentSearchResult:
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    metadata_store = SegmentMetadataStore(store)
    representative: RepresentativeRecord | None = metadata_store.get_representative(
        backend_fingerprint=backend.info.fingerprint,
        track_id=track_id,
        policy_version=policy.version,
    )
    if representative is None:
        raise ValueError(f"no representative segment for track_id {track_id}")
    identity = EmbeddingIdentity(
        backend_fingerprint=backend.info.fingerprint,
        scope="representative",
        track_id=track_id,
        start_s=representative.start_s,
        end_s=representative.end_s,
    )
    stored = store.get(identity)
    if stored is None:
        raise ValueError("representative metadata points to a missing embedding")
    selected_filters = filters or SearchFilter()
    hits, ranking_seconds = _rank_segment_query(
        store=store,
        history_path=history_path,
        backend=backend,
        query_vector=stored.vector,
        filters=selected_filters,
        top_k=top_k,
        target_scope=target_scope,
        exclude_track_id=track_id if exclude_self else None,
    )
    return SegmentSearchResult(
        query_scope="representative",
        target_scope=target_scope,
        backend_fingerprint=backend.info.fingerprint,
        query_track_id=track_id,
        start_s=representative.start_s,
        end_s=representative.end_s,
        top_k=top_k,
        embedding_seconds=0.0,
        ranking_seconds=ranking_seconds,
        cache_hit=True,
        filters=selected_filters,
        hits=hits,
    )
