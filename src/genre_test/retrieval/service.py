from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from ..track_identity import identify_track
from .backend import RetrievalBackend
from .catalog import CatalogTrack, filter_track_ids, load_catalog_tracks
from .contracts import EmbeddingIdentity, EmbeddingVector, SearchFilter, SearchHit
from .index import DenseCosineIndex
from .storage import RetrievalStore

MAX_TEXT_QUERY_CHARS = 2000
ProgressCallback = Callable[[int, int, str], None]


@dataclass(frozen=True)
class IndexRunReport:
    backend_fingerprint: str
    catalog_tracks: int
    selected_tracks: int
    available_paths: int
    missing_paths: int
    cache_hits: int
    cache_misses: int
    embedded: int
    corrupt_removed: int
    stale_embeddings: int
    path_updates: int
    failures: int
    failed_track_ids: tuple[str, ...]
    elapsed_seconds: float

    @property
    def recomputed(self) -> int:
        return self.embedded

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class IndexStatus:
    backend_fingerprint: str
    schema_version: int
    catalog_tracks: int
    available_paths: int
    missing_paths: int
    current_embeddings: int
    current_missing: int
    stale_embeddings: int
    corrupt_embeddings: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CatalogSearchHit:
    rank: int
    track_id: str
    path: str
    similarity: float
    backend_fingerprint: str
    family: str | None
    genre: str | None
    confidence: str | None
    bpm: float | None
    key: str | None
    vocal: str | None
    moods: tuple[str, ...]
    instruments: tuple[str, ...]
    production: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["moods"] = list(self.moods)
        payload["instruments"] = list(self.instruments)
        payload["production"] = list(self.production)
        return payload


@dataclass(frozen=True)
class SearchResult:
    query_type: str
    backend_fingerprint: str
    top_k: int
    embedding_seconds: float
    ranking_seconds: float
    cache_hit: bool
    query_text: str | None
    language: str | None
    query_track_id: str | None
    filters: SearchFilter
    hits: tuple[CatalogSearchHit, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "query_type": self.query_type,
            "backend_fingerprint": self.backend_fingerprint,
            "top_k": self.top_k,
            "embedding_seconds": self.embedding_seconds,
            "ranking_seconds": self.ranking_seconds,
            "cache_hit": self.cache_hit,
            "query_text": self.query_text,
            "language": self.language,
            "query_track_id": self.query_track_id,
            "filters": asdict(self.filters),
            "hits": [hit.to_dict() for hit in self.hits],
        }


def _active_identity(backend: RetrievalBackend, track_id: str) -> EmbeddingIdentity:
    return EmbeddingIdentity(
        backend_fingerprint=backend.info.fingerprint,
        scope="full",
        track_id=track_id,
    )


def _safe_cached(
    store: RetrievalStore,
    identity: EmbeddingIdentity,
) -> tuple[EmbeddingVector | None, bool]:
    try:
        stored = store.get(identity)
    except ValueError:
        store.delete_identity(identity)
        return None, False
    if stored is None:
        return None, False
    return stored.vector, True


def index_status(
    *,
    store: RetrievalStore,
    history_path: Path,
    backend_fingerprint: str,
) -> IndexStatus:
    tracks = load_catalog_tracks(history_path)
    catalog_ids = {track.track_id for track in tracks}
    current_ids = store.audio_track_ids(
        backend_fingerprint=backend_fingerprint,
        scope="full",
    ) & catalog_ids
    stale = store.count_stale(
        active_backend_fingerprint=backend_fingerprint,
        scope="full",
        track_ids=tuple(sorted(catalog_ids)),
    )
    available = sum(1 for track in tracks if track.path_exists)
    return IndexStatus(
        backend_fingerprint=backend_fingerprint,
        schema_version=store.schema_version(),
        catalog_tracks=len(tracks),
        available_paths=available,
        missing_paths=len(tracks) - available,
        current_embeddings=len(current_ids),
        current_missing=max(0, len(catalog_ids) - len(current_ids)),
        stale_embeddings=stale,
        corrupt_embeddings=len(store.corrupt_keys()),
    )


def index_catalog(
    *,
    store: RetrievalStore,
    history_path: Path,
    backend: RetrievalBackend,
    progress: ProgressCallback | None = None,
    limit: int | None = None,
) -> IndexRunReport:
    """Incrementally embed the current history catalog for one backend identity.

    Cache identity is content-addressed by track_id + backend fingerprint. A path move
    therefore updates only the stored path and never re-embeds byte-identical audio.
    Every successful vector is committed independently, so an interrupted long catalog
    run can resume without recomputing completed tracks.
    """

    if limit is not None and limit <= 0:
        raise ValueError("limit must be positive")

    started = time.perf_counter()
    all_tracks = load_catalog_tracks(history_path)
    tracks = all_tracks if limit is None else all_tracks[:limit]
    store.register_backend(backend.info)
    corrupt_removed = store.delete_corrupt()
    stale = store.count_stale(
        active_backend_fingerprint=backend.info.fingerprint,
        scope="full",
        track_ids=[track.track_id for track in all_tracks],
    )

    available_paths = 0
    missing_paths = 0
    cache_hits = 0
    cache_misses = 0
    embedded = 0
    path_updates = 0
    failed_track_ids: list[str] = []

    total = len(tracks)
    for index, track in enumerate(tracks, 1):
        if progress is not None:
            progress(index, total, track.path or track.track_id)
        if not track.path_exists:
            missing_paths += 1
            continue
        assert track.path is not None
        available_paths += 1
        identity = _active_identity(backend, track.track_id)
        try:
            stored = store.get(identity)
        except ValueError:
            store.delete_identity(identity)
            stored = None
            corrupt_removed += 1

        if stored is not None:
            cache_hits += 1
            if stored.path != track.path:
                store.update_path(identity, track.path)
                path_updates += 1
            continue

        cache_misses += 1
        try:
            vector = backend.embed_audio(Path(track.path), track_id=track.track_id)
            if vector.identity != identity:
                raise ValueError("backend returned unexpected full-track embedding identity")
            store.put(vector, backend=backend.info, path=track.path)
            embedded += 1
        except Exception:
            failed_track_ids.append(track.track_id)

    return IndexRunReport(
        backend_fingerprint=backend.info.fingerprint,
        catalog_tracks=len(all_tracks),
        selected_tracks=total,
        available_paths=available_paths,
        missing_paths=missing_paths,
        cache_hits=cache_hits,
        cache_misses=cache_misses,
        embedded=embedded,
        corrupt_removed=corrupt_removed,
        stale_embeddings=stale,
        path_updates=path_updates,
        failures=len(failed_track_ids),
        failed_track_ids=tuple(failed_track_ids),
        elapsed_seconds=time.perf_counter() - started,
    )


def rebuild_catalog(
    *,
    store: RetrievalStore,
    history_path: Path,
    backend: RetrievalBackend,
    progress: ProgressCallback | None = None,
    limit: int | None = None,
) -> IndexRunReport:
    """Rebuild only the active backend's full-track embeddings.

    Old backend fingerprints are deliberately retained as forensic/stale records.
    A limited rebuild is rejected because deleting all current vectors and rebuilding
    only a pilot prefix would leave a misleading partially rebuilt active index.
    """

    if limit is not None:
        raise ValueError("rebuild does not accept limit; use incremental index for pilots")
    store.delete_backend_scope(backend.info.fingerprint, scope="full")
    return index_catalog(
        store=store,
        history_path=history_path,
        backend=backend,
        progress=progress,
    )


def _enrich_hit(hit: SearchHit, metadata: dict[str, CatalogTrack]) -> CatalogSearchHit:
    track = metadata.get(hit.track_id)
    return CatalogSearchHit(
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


def _rank(
    *,
    store: RetrievalStore,
    history_path: Path,
    backend: RetrievalBackend,
    query_vector: EmbeddingVector,
    filters: SearchFilter,
    top_k: int,
    exclude_track_id: str | None,
) -> tuple[tuple[CatalogSearchHit, ...], float]:
    tracks = load_catalog_tracks(history_path)
    allowed = filter_track_ids(tracks, filters)
    metadata = {track.track_id: track for track in tracks}
    index = DenseCosineIndex.from_store(
        store,
        backend_fingerprint=backend.info.fingerprint,
    )
    started = time.perf_counter()
    raw_hits = index.search(
        query_vector,
        top_k=top_k,
        exclude_track_id=exclude_track_id,
        allowed_track_ids=allowed,
    )
    ranking_seconds = time.perf_counter() - started
    return tuple(_enrich_hit(hit, metadata) for hit in raw_hits), ranking_seconds


def search_audio(
    *,
    store: RetrievalStore,
    history_path: Path,
    backend: RetrievalBackend,
    audio_path: Path,
    top_k: int = 20,
    filters: SearchFilter = SearchFilter(),
    exclude_self: bool = True,
) -> SearchResult:
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    identity = identify_track(Path(audio_path))
    query_identity = _active_identity(backend, identity.track_id)

    started = time.perf_counter()
    vector, cache_hit = _safe_cached(store, query_identity)
    if vector is None:
        vector = backend.embed_audio(Path(audio_path), track_id=identity.track_id)
        if vector.identity != query_identity:
            raise ValueError("backend returned unexpected audio query embedding identity")
    embedding_seconds = time.perf_counter() - started

    hits, ranking_seconds = _rank(
        store=store,
        history_path=history_path,
        backend=backend,
        query_vector=vector,
        filters=filters,
        top_k=top_k,
        exclude_track_id=identity.track_id if exclude_self else None,
    )
    store.record_search_query(
        query_type="audio",
        backend=backend.info,
        query_track_id=identity.track_id,
        top_k=top_k,
        filters=asdict(filters),
        embedding_seconds=embedding_seconds,
        ranking_seconds=ranking_seconds,
        result_count=len(hits),
    )
    return SearchResult(
        query_type="audio",
        backend_fingerprint=backend.info.fingerprint,
        top_k=top_k,
        embedding_seconds=embedding_seconds,
        ranking_seconds=ranking_seconds,
        cache_hit=cache_hit,
        query_text=None,
        language=None,
        query_track_id=identity.track_id,
        filters=filters,
        hits=hits,
    )


def search_text(
    *,
    store: RetrievalStore,
    history_path: Path,
    backend: RetrievalBackend,
    text: str,
    language: str | None = None,
    top_k: int = 20,
    filters: SearchFilter = SearchFilter(),
) -> SearchResult:
    normalized = text.strip()
    if not normalized:
        raise ValueError("text query must not be empty")
    if len(normalized) > MAX_TEXT_QUERY_CHARS:
        raise ValueError(
            f"text query is too long: {len(normalized)} > {MAX_TEXT_QUERY_CHARS} characters"
        )
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    identity = EmbeddingIdentity.for_text(
        backend.info.fingerprint,
        normalized,
        language=language,
    )
    started = time.perf_counter()
    vector, cache_hit = _safe_cached(store, identity)
    if vector is None:
        vector = backend.embed_text(normalized, language=language)
        if vector.identity != identity:
            raise ValueError("backend returned unexpected text embedding identity")
        store.put(vector, backend=backend.info)
    embedding_seconds = time.perf_counter() - started

    hits, ranking_seconds = _rank(
        store=store,
        history_path=history_path,
        backend=backend,
        query_vector=vector,
        filters=filters,
        top_k=top_k,
        exclude_track_id=None,
    )
    store.record_search_query(
        query_type="text",
        backend=backend.info,
        query_text=normalized,
        language=identity.language,
        top_k=top_k,
        filters=asdict(filters),
        embedding_seconds=embedding_seconds,
        ranking_seconds=ranking_seconds,
        result_count=len(hits),
    )
    return SearchResult(
        query_type="text",
        backend_fingerprint=backend.info.fingerprint,
        top_k=top_k,
        embedding_seconds=embedding_seconds,
        ranking_seconds=ranking_seconds,
        cache_hit=cache_hit,
        query_text=normalized,
        language=identity.language,
        query_track_id=None,
        filters=filters,
        hits=hits,
    )
