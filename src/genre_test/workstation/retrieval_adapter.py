from __future__ import annotations

import importlib
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

RetrievalState = Literal["OK", "WARN", "N/A"]


@dataclass(frozen=True)
class WorkstationRetrievalStatus:
    status: RetrievalState
    available: bool
    code: str | None
    message: str | None
    history_path: str
    store_path: str
    backend_fingerprint: str | None
    backend: dict[str, Any] | None
    index: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _unavailable(
    *,
    code: str,
    message: str,
    history_path: Path,
    store_path: Path,
    backend_fingerprint: str | None = None,
    backend: dict[str, Any] | None = None,
) -> WorkstationRetrievalStatus:
    return WorkstationRetrievalStatus(
        status="N/A",
        available=False,
        code=code,
        message=message,
        history_path=str(history_path),
        store_path=str(store_path),
        backend_fingerprint=backend_fingerprint,
        backend=backend,
        index=None,
    )


def _validate_existing_store(store_path: Path, expected_schema_version: int) -> None:
    """Validate an existing retrieval store without creating or migrating it."""

    uri = f"{store_path.resolve().as_uri()}?mode=ro"
    with sqlite3.connect(uri, uri=True, timeout=5) as connection:
        table_rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        tables = {str(row[0]) for row in table_rows}
        required_tables = {
            "retrieval_meta",
            "embedding_models",
            "embeddings",
            "search_queries",
        }
        if not required_tables.issubset(tables):
            raise ValueError("retrieval store schema is incomplete")

        row = connection.execute(
            "SELECT value FROM retrieval_meta WHERE key = 'schema_version'"
        ).fetchone()
        if row is None:
            raise ValueError("retrieval store schema version is missing")
        try:
            schema_version = int(row[0])
        except (TypeError, ValueError) as exc:
            raise ValueError("retrieval store schema version is invalid") from exc
        if schema_version != expected_schema_version:
            raise ValueError(
                "retrieval store schema version is incompatible: "
                f"{schema_version} != {expected_schema_version}"
            )


def collect_retrieval_status() -> dict[str, Any]:
    """Read canonical retrieval state without starting the CLaMP sidecar.

    Imports stay inside this call so importing/starting the Workstation shell remains
    independent from optional retrieval modules. Missing or invalid state files are
    reported as ``N/A`` before ``RetrievalStore`` is constructed, preventing a status
    request from creating or migrating a database that could masquerade as a valid
    empty index.
    """

    runtime_meta = importlib.import_module("genre_test.runtime_meta")
    history_source = importlib.import_module("genre_test.retrieval.history_source")
    clamp_backend = importlib.import_module("genre_test.retrieval.clamp3_sidecar_backend")
    retrieval_service = importlib.import_module("genre_test.retrieval.service")
    storage = importlib.import_module("genre_test.retrieval.storage")

    state_dir = Path(runtime_meta.default_state_dir())
    history_path = Path(runtime_meta.default_history_path())
    store_path = state_dir / "retrieval.sqlite3"
    backend_info = clamp_backend.default_clamp3_backend_info()
    backend_payload = backend_info.to_dict()
    backend_fingerprint = backend_info.fingerprint

    if not history_path.is_file():
        return _unavailable(
            code="history_source_missing",
            message="analysis history is unavailable",
            history_path=history_path,
            store_path=store_path,
            backend_fingerprint=backend_fingerprint,
            backend=backend_payload,
        ).to_dict()

    history_error = history_source.HistorySourceError
    try:
        history_source.validate_explicit_history(history_path)
    except history_error as exc:
        failure = exc.to_dict()
        return _unavailable(
            code=str(failure.get("code") or "history_source_unavailable"),
            message=str(failure.get("message") or "analysis history is unavailable"),
            history_path=history_path,
            store_path=store_path,
            backend_fingerprint=backend_fingerprint,
            backend=backend_payload,
        ).to_dict()

    if not store_path.is_file():
        return _unavailable(
            code="retrieval_store_missing",
            message="retrieval index store has not been created yet",
            history_path=history_path,
            store_path=store_path,
            backend_fingerprint=backend_fingerprint,
            backend=backend_payload,
        ).to_dict()

    try:
        _validate_existing_store(store_path, int(storage.SCHEMA_VERSION))
        store = storage.RetrievalStore(store_path)
        index = retrieval_service.index_status(
            store=store,
            history_path=history_path,
            backend_fingerprint=backend_fingerprint,
        )
        index_payload = index.to_dict()
    except (OSError, RuntimeError, ValueError, sqlite3.Error) as exc:
        return _unavailable(
            code="retrieval_status_unavailable",
            message=f"retrieval status could not be read: {type(exc).__name__}",
            history_path=history_path,
            store_path=store_path,
            backend_fingerprint=backend_fingerprint,
            backend=backend_payload,
        ).to_dict()

    degraded = any(
        int(index_payload.get(key, 0) or 0) > 0
        for key in (
            "current_missing",
            "stale_embeddings",
            "corrupt_embeddings",
            "missing_paths",
        )
    )
    return WorkstationRetrievalStatus(
        status="WARN" if degraded else "OK",
        available=True,
        code=None,
        message=None,
        history_path=str(history_path),
        store_path=str(store_path),
        backend_fingerprint=backend_fingerprint,
        backend=backend_payload,
        index=index_payload,
    ).to_dict()
