from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

from .backend import RetrievalBackend
from .catalog import CatalogTrack, load_catalog_tracks
from .contracts import EmbeddingIdentity
from .storage import RetrievalStore


@dataclass(frozen=True)
class CatalogAcceptanceReport:
    backend_fingerprint: str
    catalog_tracks: int
    readable_paths: int
    missing_paths: int
    current_embeddings: int
    readable_without_embedding: int
    stale_embeddings: int
    corrupt_embeddings: int
    current_coverage: float
    retrieval_db_bytes: int
    missing_track_ids: tuple[str, ...]
    retry_track_ids: tuple[str, ...]
    by_family: dict[str, int]
    by_genre: dict[str, int]
    by_folder: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["missing_track_ids"] = list(self.missing_track_ids)
        payload["retry_track_ids"] = list(self.retry_track_ids)
        return payload


def catalog_acceptance_report(
    *,
    store: RetrievalStore,
    history_path: Path,
    backend_fingerprint: str,
) -> CatalogAcceptanceReport:
    tracks = load_catalog_tracks(history_path)
    current_ids = store.audio_track_ids(
        backend_fingerprint=backend_fingerprint,
        scope="full",
    )
    readable = [track for track in tracks if track.path_exists]
    missing = [track for track in tracks if not track.path_exists]
    retry = [track for track in readable if track.track_id not in current_ids]
    coverage = (
        len(current_ids & {track.track_id for track in readable}) / len(readable)
        if readable
        else 0.0
    )

    family_counts = Counter((track.family or "UNKNOWN") for track in tracks)
    genre_counts = Counter((track.genre or "UNKNOWN") for track in tracks)
    folder_counts = Counter(
        str(Path(track.path).parent) if track.path else "MISSING"
        for track in tracks
    )

    return CatalogAcceptanceReport(
        backend_fingerprint=backend_fingerprint,
        catalog_tracks=len(tracks),
        readable_paths=len(readable),
        missing_paths=len(missing),
        current_embeddings=len(current_ids),
        readable_without_embedding=len(retry),
        stale_embeddings=store.count_stale(
            active_backend_fingerprint=backend_fingerprint,
            scope="full",
            track_ids=[track.track_id for track in tracks],
        ),
        corrupt_embeddings=len(store.corrupt_keys()),
        current_coverage=coverage,
        retrieval_db_bytes=store.path.stat().st_size if store.path.exists() else 0,
        missing_track_ids=tuple(track.track_id for track in missing),
        retry_track_ids=tuple(track.track_id for track in retry),
        by_family=dict(sorted(family_counts.items())),
        by_genre=dict(sorted(genre_counts.items())),
        by_folder=dict(sorted(folder_counts.items())),
    )


def retry_missing_full_embeddings(
    *,
    store: RetrievalStore,
    history_path: Path,
    backend: RetrievalBackend,
    track_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    tracks = load_catalog_tracks(history_path)
    selected_ids = (
        set(track_ids)
        if track_ids is not None
        else set(
            catalog_acceptance_report(
                store=store,
                history_path=history_path,
                backend_fingerprint=backend.info.fingerprint,
            ).retry_track_ids
        )
    )
    by_id: dict[str, CatalogTrack] = {track.track_id: track for track in tracks}
    embedded = 0
    skipped_missing = 0
    already_cached = 0
    failures: list[str] = []

    for track_id in sorted(selected_ids):
        track = by_id.get(track_id)
        if track is None or track.path is None or not track.path_exists:
            skipped_missing += 1
            continue
        identity = EmbeddingIdentity(
            backend_fingerprint=backend.info.fingerprint,
            scope="full",
            track_id=track.track_id,
        )
        try:
            cached = store.get(identity)
        except ValueError:
            store.delete_identity(identity)
            cached = None
        if cached is not None:
            already_cached += 1
            continue
        try:
            vector = backend.embed_audio(Path(track.path), track_id=track.track_id)
            if vector.identity != identity:
                raise ValueError("backend returned unexpected full-track identity")
            store.put(vector, backend=backend.info, path=track.path)
            embedded += 1
        except (OSError, RuntimeError, ValueError):
            failures.append(track.track_id)

    return {
        "backend_fingerprint": backend.info.fingerprint,
        "requested": len(selected_ids),
        "embedded": embedded,
        "already_cached": already_cached,
        "skipped_missing": skipped_missing,
        "failed": len(failures),
        "failed_track_ids": failures,
    }


def write_catalog_acceptance_reports(
    report: CatalogAcceptanceReport,
    prefix: Path,
) -> dict[str, Path]:
    target = Path(prefix)
    target.parent.mkdir(parents=True, exist_ok=True)
    json_path = target.with_suffix(".json")
    md_path = target.with_suffix(".md")

    json_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Retrieval catalog acceptance",
        "",
        f"Backend fingerprint: `{report.backend_fingerprint}`",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Catalog tracks | {report.catalog_tracks} |",
        f"| Readable paths | {report.readable_paths} |",
        f"| Missing paths | {report.missing_paths} |",
        f"| Current full embeddings | {report.current_embeddings} |",
        f"| Readable without embedding | {report.readable_without_embedding} |",
        f"| Stale embeddings | {report.stale_embeddings} |",
        f"| Corrupt embeddings | {report.corrupt_embeddings} |",
        f"| Coverage | {report.current_coverage:.4%} |",
        f"| retrieval.sqlite3 bytes | {report.retrieval_db_bytes} |",
        "",
        "## Acceptance interpretation",
        "",
        "Release target: >=99% of readable source files indexed, or every failure individually explained.",
        "A second unchanged indexing pass must report zero recomputation and cache hits for all indexed rows.",
        "Retrieval failures do not invalidate existing v0.4 AudioProfile rows.",
        "",
        "## Backup / restore",
        "",
        "1. Stop Genre_test/retrieval sidecar before copying the DB.",
        "2. Copy `.genre_test/retrieval.sqlite3` together with any `-wal` / `-shm` files if they exist.",
        "3. For a clean SQLite backup, prefer the SQLite backup API or copy after all processes are closed.",
        "4. Restore only with the application stopped; keep the original backup until status/audit passes.",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": json_path, "markdown": md_path}
