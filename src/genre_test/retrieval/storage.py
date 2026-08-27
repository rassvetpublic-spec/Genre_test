from __future__ import annotations

import hashlib
import json
import sqlite3
import struct
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import EmbeddingIdentity, EmbeddingVector, RetrievalBackendInfo

SCHEMA_VERSION = 2


@dataclass(frozen=True)
class StoredEmbedding:
    cache_key: str
    identity: EmbeddingIdentity
    path: str | None
    vector: EmbeddingVector
    vector_sha256: str
    created_at: str


@dataclass(frozen=True)
class SearchQueryRecord:
    query_id: int
    query_type: str
    backend_fingerprint: str
    query_text: str | None
    language: str | None
    query_track_id: str | None
    top_k: int
    filters: dict[str, Any]
    embedding_seconds: float
    ranking_seconds: float
    result_count: int
    created_at: str


def _pack_f32(values: tuple[float, ...]) -> bytes:
    return struct.pack(f"<{len(values)}f", *values)


def _unpack_f32(payload: bytes, dimension: int) -> tuple[float, ...]:
    expected = dimension * 4
    if len(payload) != expected:
        raise ValueError(
            f"corrupt embedding payload: expected {expected} bytes, got {len(payload)}"
        )
    return tuple(struct.unpack(f"<{dimension}f", payload))


class RetrievalStore:
    """SQLite-backed persistent cache for normalized retrieval embeddings."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS retrieval_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS embedding_models (
                    fingerprint TEXT PRIMARY KEY,
                    backend_name TEXT NOT NULL,
                    backend_version TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS embeddings (
                    cache_key TEXT PRIMARY KEY,
                    backend_fingerprint TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    track_id TEXT,
                    text_sha256 TEXT,
                    language TEXT,
                    start_s REAL,
                    end_s REAL,
                    path TEXT,
                    dimension INTEGER NOT NULL,
                    vector_blob BLOB NOT NULL,
                    vector_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (backend_fingerprint)
                        REFERENCES embedding_models(fingerprint)
                );

                CREATE INDEX IF NOT EXISTS idx_embeddings_track
                    ON embeddings(track_id, backend_fingerprint, scope);

                CREATE INDEX IF NOT EXISTS idx_embeddings_backend_scope
                    ON embeddings(backend_fingerprint, scope);
                """
            )
            row = connection.execute(
                "SELECT value FROM retrieval_meta WHERE key = 'schema_version'"
            ).fetchone()
            if row is None:
                current_version = 1
                connection.execute(
                    "INSERT INTO retrieval_meta(key, value) VALUES('schema_version', ?)",
                    (str(current_version),),
                )
            else:
                current_version = int(row["value"])

            if current_version > SCHEMA_VERSION:
                raise RuntimeError(
                    f"unsupported retrieval schema version {current_version}; "
                    f"expected <= {SCHEMA_VERSION}"
                )
            self._migrate(connection, current_version)

    @staticmethod
    def _migrate(connection: sqlite3.Connection, current_version: int) -> None:
        version = current_version
        if version < 2:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS search_queries (
                    query_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_type TEXT NOT NULL,
                    backend_fingerprint TEXT NOT NULL,
                    query_text TEXT,
                    language TEXT,
                    query_track_id TEXT,
                    top_k INTEGER NOT NULL,
                    filters_json TEXT NOT NULL,
                    embedding_seconds REAL NOT NULL,
                    ranking_seconds REAL NOT NULL,
                    result_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (backend_fingerprint)
                        REFERENCES embedding_models(fingerprint)
                );

                CREATE INDEX IF NOT EXISTS idx_search_queries_backend_time
                    ON search_queries(backend_fingerprint, created_at DESC, query_id DESC);
                """
            )
            version = 2
            connection.execute(
                "UPDATE retrieval_meta SET value = ? WHERE key = 'schema_version'",
                (str(version),),
            )

        if version != SCHEMA_VERSION:
            raise RuntimeError(
                f"retrieval schema migration stopped at {version}; expected {SCHEMA_VERSION}"
            )

    def schema_version(self) -> int:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT value FROM retrieval_meta WHERE key = 'schema_version'"
            ).fetchone()
        if row is None:
            raise RuntimeError("retrieval schema version is missing")
        return int(row["value"])

    def register_backend(self, info: RetrievalBackendInfo) -> None:
        payload = json.dumps(
            info.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO embedding_models(
                    fingerprint, backend_name, backend_version, payload_json
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(fingerprint) DO UPDATE SET
                    backend_name=excluded.backend_name,
                    backend_version=excluded.backend_version,
                    payload_json=excluded.payload_json
                """,
                (info.fingerprint, info.backend_name, info.backend_version, payload),
            )

    def put(
        self,
        vector: EmbeddingVector,
        *,
        backend: RetrievalBackendInfo,
        path: str | None = None,
    ) -> str:
        if vector.identity.backend_fingerprint != backend.fingerprint:
            raise ValueError("embedding identity does not match backend fingerprint")
        if vector.dimension != backend.embedding_dim:
            raise ValueError(
                f"embedding dimension mismatch: backend={backend.embedding_dim}, "
                f"vector={vector.dimension}"
            )
        if vector.identity.scope != "text" and not path:
            raise ValueError("audio embeddings require a source path")

        self.register_backend(backend)
        blob = _pack_f32(vector.values)
        vector_sha256 = hashlib.sha256(blob).hexdigest()
        identity = vector.identity

        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO embeddings(
                    cache_key, backend_fingerprint, scope, track_id, text_sha256,
                    language, start_s, end_s, path, dimension, vector_blob, vector_sha256
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    path=excluded.path,
                    dimension=excluded.dimension,
                    vector_blob=excluded.vector_blob,
                    vector_sha256=excluded.vector_sha256
                """,
                (
                    identity.cache_key,
                    identity.backend_fingerprint,
                    identity.scope,
                    identity.track_id,
                    identity.text_sha256,
                    identity.language,
                    identity.start_s,
                    identity.end_s,
                    path,
                    vector.dimension,
                    blob,
                    vector_sha256,
                ),
            )
        return vector_sha256

    def get(self, identity: EmbeddingIdentity) -> StoredEmbedding | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM embeddings WHERE cache_key = ?",
                (identity.cache_key,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_embedding(row, expected_identity=identity)

    def update_path(self, identity: EmbeddingIdentity, path: str) -> bool:
        if identity.scope == "text":
            raise ValueError("text embeddings do not have source paths")
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE embeddings SET path = ? WHERE cache_key = ?",
                (path, identity.cache_key),
            )
        return cursor.rowcount > 0

    def delete_identity(self, identity: EmbeddingIdentity) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                "DELETE FROM embeddings WHERE cache_key = ?",
                (identity.cache_key,),
            )
        return cursor.rowcount > 0

    def delete_backend_scope(self, backend_fingerprint: str, *, scope: str = "full") -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                "DELETE FROM embeddings WHERE backend_fingerprint = ? AND scope = ?",
                (backend_fingerprint, scope),
            )
        return int(cursor.rowcount)

    def iter_audio(
        self,
        *,
        backend_fingerprint: str,
        scope: str = "full",
    ) -> list[StoredEmbedding]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM embeddings
                WHERE backend_fingerprint = ?
                  AND scope = ?
                  AND track_id IS NOT NULL
                ORDER BY track_id, path, cache_key
                """,
                (backend_fingerprint, scope),
            ).fetchall()
        return [self._row_to_embedding(row) for row in rows]

    def audio_track_ids(
        self,
        *,
        backend_fingerprint: str,
        scope: str = "full",
    ) -> set[str]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT track_id FROM embeddings
                WHERE backend_fingerprint = ?
                  AND scope = ?
                  AND track_id IS NOT NULL
                """,
                (backend_fingerprint, scope),
            ).fetchall()
        return {str(row["track_id"]) for row in rows}

    def backend_fingerprints(self, *, scope: str | None = None) -> tuple[str, ...]:
        sql = "SELECT DISTINCT backend_fingerprint FROM embeddings"
        params: tuple[str, ...] = ()
        if scope is not None:
            sql += " WHERE scope = ?"
            params = (scope,)
        sql += " ORDER BY backend_fingerprint"
        with self.connect() as connection:
            rows = connection.execute(sql, params).fetchall()
        return tuple(str(row["backend_fingerprint"]) for row in rows)

    def count_stale(
        self,
        *,
        active_backend_fingerprint: str,
        scope: str = "full",
        track_ids: Sequence[str] | None = None,
    ) -> int:
        if track_ids is not None and not track_ids:
            return 0
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT track_id FROM embeddings
                WHERE scope = ?
                  AND backend_fingerprint != ?
                  AND track_id IS NOT NULL
                """,
                (scope, active_backend_fingerprint),
            ).fetchall()
        if track_ids is None:
            return len(rows)
        requested = set(track_ids)
        return sum(1 for row in rows if str(row["track_id"]) in requested)

    def corrupt_keys(self) -> tuple[str, ...]:
        corrupt: list[str] = []
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM embeddings ORDER BY cache_key").fetchall()
        for row in rows:
            try:
                self._row_to_embedding(row)
            except ValueError:
                corrupt.append(str(row["cache_key"]))
        return tuple(corrupt)

    def delete_corrupt(self) -> int:
        corrupt_keys = self.corrupt_keys()
        if not corrupt_keys:
            return 0
        with self.connect() as connection:
            connection.executemany(
                "DELETE FROM embeddings WHERE cache_key = ?",
                [(key,) for key in corrupt_keys],
            )
        return len(corrupt_keys)

    def stats(self, *, backend_fingerprint: str | None = None) -> dict[str, int]:
        sql = "SELECT scope, COUNT(*) AS n FROM embeddings"
        params: tuple[str, ...] = ()
        if backend_fingerprint is not None:
            sql += " WHERE backend_fingerprint = ?"
            params = (backend_fingerprint,)
        sql += " GROUP BY scope"
        with self.connect() as connection:
            rows = connection.execute(sql, params).fetchall()
        counts = {str(row["scope"]): int(row["n"]) for row in rows}
        counts["total"] = sum(counts.values())
        return counts

    def record_search_query(
        self,
        *,
        query_type: str,
        backend: RetrievalBackendInfo,
        top_k: int,
        filters: dict[str, Any],
        embedding_seconds: float,
        ranking_seconds: float,
        result_count: int,
        query_text: str | None = None,
        language: str | None = None,
        query_track_id: str | None = None,
    ) -> int:
        if query_type not in {"text", "audio"}:
            raise ValueError("query_type must be text or audio")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        if query_type == "text" and not query_text:
            raise ValueError("text query history requires query_text")
        if query_type == "audio" and not query_track_id:
            raise ValueError("audio query history requires query_track_id")
        self.register_backend(backend)
        filters_json = json.dumps(
            filters,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO search_queries(
                    query_type, backend_fingerprint, query_text, language,
                    query_track_id, top_k, filters_json, embedding_seconds,
                    ranking_seconds, result_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    query_type,
                    backend.fingerprint,
                    query_text,
                    language,
                    query_track_id,
                    top_k,
                    filters_json,
                    float(embedding_seconds),
                    float(ranking_seconds),
                    int(result_count),
                ),
            )
            query_id = cursor.lastrowid
        if query_id is None:
            raise RuntimeError("failed to record search query")
        return int(query_id)

    def search_history(self, *, limit: int = 50) -> list[SearchQueryRecord]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM search_queries
                ORDER BY query_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            SearchQueryRecord(
                query_id=int(row["query_id"]),
                query_type=str(row["query_type"]),
                backend_fingerprint=str(row["backend_fingerprint"]),
                query_text=row["query_text"],
                language=row["language"],
                query_track_id=row["query_track_id"],
                top_k=int(row["top_k"]),
                filters=json.loads(str(row["filters_json"])),
                embedding_seconds=float(row["embedding_seconds"]),
                ranking_seconds=float(row["ranking_seconds"]),
                result_count=int(row["result_count"]),
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]

    def _row_to_embedding(
        self,
        row: sqlite3.Row,
        *,
        expected_identity: EmbeddingIdentity | None = None,
    ) -> StoredEmbedding:
        identity = EmbeddingIdentity(
            backend_fingerprint=str(row["backend_fingerprint"]),
            scope=str(row["scope"]),  # type: ignore[arg-type]
            track_id=row["track_id"],
            text_sha256=row["text_sha256"],
            language=row["language"],
            start_s=row["start_s"],
            end_s=row["end_s"],
        )
        if expected_identity is not None and identity != expected_identity:
            raise ValueError("stored embedding identity mismatch")

        blob = bytes(row["vector_blob"])
        digest = hashlib.sha256(blob).hexdigest()
        if digest != row["vector_sha256"]:
            raise ValueError(f"corrupt embedding vector for cache key {row['cache_key']}")

        values = _unpack_f32(blob, int(row["dimension"]))
        vector = EmbeddingVector.normalized(
            identity,
            values,
            expected_dim=int(row["dimension"]),
        )
        return StoredEmbedding(
            cache_key=str(row["cache_key"]),
            identity=identity,
            path=row["path"],
            vector=vector,
            vector_sha256=str(row["vector_sha256"]),
            created_at=str(row["created_at"]),
        )
