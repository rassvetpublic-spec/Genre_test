from __future__ import annotations

import hashlib
import json
import sqlite3
import struct
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .contracts import EmbeddingIdentity, EmbeddingVector, RetrievalBackendInfo

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class StoredEmbedding:
    cache_key: str
    identity: EmbeddingIdentity
    path: str | None
    vector: EmbeddingVector
    vector_sha256: str
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
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys = ON")
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
                connection.execute(
                    "INSERT INTO retrieval_meta(key, value) VALUES('schema_version', ?)",
                    (str(SCHEMA_VERSION),),
                )
            elif int(row["value"]) != SCHEMA_VERSION:
                raise RuntimeError(
                    f"unsupported retrieval schema version {row['value']}; "
                    f"expected {SCHEMA_VERSION}"
                )

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
                ORDER BY track_id, cache_key
                """,
                (backend_fingerprint, scope),
            ).fetchall()
        return [self._row_to_embedding(row) for row in rows]

    def delete_corrupt(self) -> int:
        corrupt_keys: list[str] = []
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM embeddings").fetchall()
        for row in rows:
            try:
                self._row_to_embedding(row)
            except ValueError:
                corrupt_keys.append(str(row["cache_key"]))

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
