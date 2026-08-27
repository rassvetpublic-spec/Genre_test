from __future__ import annotations

from dataclasses import dataclass

from .storage import RetrievalStore

SEGMENT_EXTENSION_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class RepresentativeRecord:
    backend_fingerprint: str
    track_id: str
    policy_version: str
    start_s: float
    end_s: float
    score: float
    segment_cache_key: str
    representative_cache_key: str
    updated_at: str


class SegmentMetadataStore:
    """Versioned segment metadata extension inside retrieval.sqlite3.

    Embedding payloads remain owned by RetrievalStore. This extension stores only
    the representative-selection decision and its policy identity.
    """

    def __init__(self, store: RetrievalStore) -> None:
        self.store = store
        self._initialize()

    def _initialize(self) -> None:
        with self.store.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS segment_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS segment_representatives (
                    backend_fingerprint TEXT NOT NULL,
                    track_id TEXT NOT NULL,
                    policy_version TEXT NOT NULL,
                    start_s REAL NOT NULL,
                    end_s REAL NOT NULL,
                    score REAL NOT NULL,
                    segment_cache_key TEXT NOT NULL,
                    representative_cache_key TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (backend_fingerprint, track_id, policy_version)
                );

                CREATE INDEX IF NOT EXISTS idx_segment_representatives_backend
                    ON segment_representatives(backend_fingerprint, policy_version, track_id);
                """
            )
            row = connection.execute(
                "SELECT value FROM segment_meta WHERE key = 'schema_version'"
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO segment_meta(key, value) VALUES('schema_version', ?)",
                    (str(SEGMENT_EXTENSION_SCHEMA_VERSION),),
                )
            elif int(row["value"]) != SEGMENT_EXTENSION_SCHEMA_VERSION:
                raise RuntimeError(
                    "unsupported segment extension schema version "
                    f"{row['value']}; expected {SEGMENT_EXTENSION_SCHEMA_VERSION}"
                )

    def schema_version(self) -> int:
        with self.store.connect() as connection:
            row = connection.execute(
                "SELECT value FROM segment_meta WHERE key = 'schema_version'"
            ).fetchone()
        if row is None:
            raise RuntimeError("segment extension schema version is missing")
        return int(row["value"])

    def replace_representative(
        self,
        *,
        backend_fingerprint: str,
        track_id: str,
        policy_version: str,
        start_s: float,
        end_s: float,
        score: float,
        segment_cache_key: str,
        representative_cache_key: str,
    ) -> None:
        with self.store.connect() as connection:
            connection.execute(
                """
                DELETE FROM embeddings
                WHERE backend_fingerprint = ?
                  AND track_id = ?
                  AND scope = 'representative'
                  AND cache_key != ?
                """,
                (backend_fingerprint, track_id, representative_cache_key),
            )
            connection.execute(
                """
                INSERT INTO segment_representatives(
                    backend_fingerprint, track_id, policy_version,
                    start_s, end_s, score, segment_cache_key,
                    representative_cache_key, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(backend_fingerprint, track_id, policy_version) DO UPDATE SET
                    start_s=excluded.start_s,
                    end_s=excluded.end_s,
                    score=excluded.score,
                    segment_cache_key=excluded.segment_cache_key,
                    representative_cache_key=excluded.representative_cache_key,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    backend_fingerprint,
                    track_id,
                    policy_version,
                    float(start_s),
                    float(end_s),
                    float(score),
                    segment_cache_key,
                    representative_cache_key,
                ),
            )

    def get_representative(
        self,
        *,
        backend_fingerprint: str,
        track_id: str,
        policy_version: str,
    ) -> RepresentativeRecord | None:
        with self.store.connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM segment_representatives
                WHERE backend_fingerprint = ? AND track_id = ? AND policy_version = ?
                """,
                (backend_fingerprint, track_id, policy_version),
            ).fetchone()
        if row is None:
            return None
        return self._row(row)

    def list_representatives(
        self,
        *,
        backend_fingerprint: str,
        policy_version: str,
    ) -> list[RepresentativeRecord]:
        with self.store.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM segment_representatives
                WHERE backend_fingerprint = ? AND policy_version = ?
                ORDER BY track_id
                """,
                (backend_fingerprint, policy_version),
            ).fetchall()
        return [self._row(row) for row in rows]

    @staticmethod
    def _row(row: object) -> RepresentativeRecord:
        values = row  # sqlite3.Row supports mapping access; keep sqlite import out of public API.
        return RepresentativeRecord(
            backend_fingerprint=str(values["backend_fingerprint"]),  # type: ignore[index]
            track_id=str(values["track_id"]),  # type: ignore[index]
            policy_version=str(values["policy_version"]),  # type: ignore[index]
            start_s=float(values["start_s"]),  # type: ignore[index]
            end_s=float(values["end_s"]),  # type: ignore[index]
            score=float(values["score"]),  # type: ignore[index]
            segment_cache_key=str(values["segment_cache_key"]),  # type: ignore[index]
            representative_cache_key=str(values["representative_cache_key"]),  # type: ignore[index]
            updated_at=str(values["updated_at"]),  # type: ignore[index]
        )
