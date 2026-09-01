from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from ..db_access_journal import create_database_provenance, record_database_access

DuplicatePolicy = Literal["error", "latest"]
_SCOPE_META_TABLE = "retrieval_history_scope_meta"


@dataclass(frozen=True)
class ScopeBuildReport:
    source: str
    output: str
    source_fingerprint: str
    analyzer_version: str
    analysis_mode: str
    duplicate_policy: str
    matching_runs: int
    duplicate_track_ids: int
    selected_tracks: int
    integrity_check: str
    source_unchanged: bool
    journal: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _source_fingerprint(path: Path) -> str:
    """Hash the SQLite DB plus any non-empty WAL, excluding volatile SHM state.

    SQLite can create a zero-length ``-wal`` and refresh ``-shm`` metadata when a
    WAL-mode database is opened read-only. Those side effects do not represent a
    logical source change, so an empty WAL is normalized to the same state as no WAL.
    A non-empty WAL remains part of the fingerprint because it can contain committed
    pages that are not yet checkpointed into the main DB file.
    """

    digest = hashlib.sha256()
    candidates = [path]
    wal = path.with_name(path.name + "-wal")
    try:
        if wal.is_file() and wal.stat().st_size > 0:
            candidates.append(wal)
    except OSError:
        candidates.append(wal)

    for candidate in candidates:
        digest.update(candidate.name.encode("utf-8", errors="surrogatepass"))
        digest.update(b"\0")
        digest.update(_hash_file(candidate).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _connect_read_only(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _columns(connection: sqlite3.Connection, table: str) -> list[str]:
    return [
        str(row["name"])
        for row in connection.execute(
            f"PRAGMA table_info({_quote_identifier(table)})"
        ).fetchall()
    ]


def _table_schema(connection: sqlite3.Connection, table: str) -> str:
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    if row is None or not row["sql"]:
        raise ValueError(f"source history is missing required table: {table}")
    return str(row["sql"])


def _index_schemas(connection: sqlite3.Connection, tables: tuple[str, ...]) -> list[str]:
    placeholders = ",".join("?" for _ in tables)
    rows = connection.execute(
        f"""
        SELECT sql
        FROM sqlite_master
        WHERE type='index'
          AND tbl_name IN ({placeholders})
          AND sql IS NOT NULL
        ORDER BY name
        """,
        tables,
    ).fetchall()
    return [str(row["sql"]) for row in rows if row["sql"]]


def _validate_scope_inputs(
    source: Path,
    output: Path,
    analyzer_version: str,
    analysis_mode: str,
    duplicate_policy: DuplicatePolicy,
) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"source history not found: {source}")
    if source.resolve() == output.resolve():
        raise ValueError("output must not overwrite the source history")
    if not analyzer_version.strip():
        raise ValueError("analyzer_version must not be empty")
    if not analysis_mode.strip():
        raise ValueError("analysis_mode must not be empty")
    if duplicate_policy not in {"error", "latest"}:
        raise ValueError("duplicate_policy must be error or latest")


def build_history_scope(
    source: Path,
    output: Path,
    *,
    analyzer_version: str,
    analysis_mode: str,
    duplicate_policy: DuplicatePolicy = "error",
    force: bool = False,
) -> ScopeBuildReport:
    """Build a retrieval-only SQLite snapshot for one analyzer version/mode scope."""

    source = Path(source).expanduser().resolve()
    output = Path(output).expanduser().resolve()
    _validate_scope_inputs(source, output, analyzer_version, analysis_mode, duplicate_policy)
    if output.exists() and not force:
        raise FileExistsError(f"output already exists: {output}")

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + f".tmp-{uuid.uuid4().hex}")
    source_fingerprint_before = _source_fingerprint(source)

    source_connection: sqlite3.Connection | None = None
    destination: sqlite3.Connection | None = None
    try:
        source_connection = _connect_read_only(source)
        track_columns = _columns(source_connection, "tracks")
        run_columns = _columns(source_connection, "runs")
        required_run_columns = {
            "track_id",
            "analyzed_at",
            "analyzer_version",
            "analysis_mode",
            "source_path",
            "result_json",
        }
        missing_columns = required_run_columns - set(run_columns)
        if missing_columns:
            raise ValueError(
                "source runs table is missing required columns: "
                + ", ".join(sorted(missing_columns))
            )
        if "track_id" not in track_columns or "last_path" not in track_columns:
            raise ValueError("source tracks table must contain track_id and last_path")

        matching_runs = int(
            source_connection.execute(
                """
                SELECT COUNT(*)
                FROM runs
                WHERE analyzer_version=? AND analysis_mode=?
                """,
                (analyzer_version, analysis_mode),
            ).fetchone()[0]
        )
        if matching_runs == 0:
            raise ValueError(
                "scope matched zero runs: "
                f"analyzer_version={analyzer_version!r}, analysis_mode={analysis_mode!r}"
            )

        duplicate_rows = source_connection.execute(
            """
            SELECT track_id, COUNT(*) AS n
            FROM runs
            WHERE analyzer_version=? AND analysis_mode=?
            GROUP BY track_id
            HAVING COUNT(*) > 1
            ORDER BY track_id
            """,
            (analyzer_version, analysis_mode),
        ).fetchall()
        duplicate_track_ids = len(duplicate_rows)
        if duplicate_track_ids and duplicate_policy == "error":
            preview = ", ".join(str(row["track_id"]) for row in duplicate_rows[:5])
            raise ValueError(
                f"scope contains {duplicate_track_ids} duplicate track_id values; "
                f"rerun with --duplicate-policy latest only after review. First: {preview}"
            )

        quoted_run_columns = ", ".join(_quote_identifier(name) for name in run_columns)
        if duplicate_policy == "latest":
            selection_sql = f"""
                SELECT {quoted_run_columns}
                FROM (
                    SELECT
                        {quoted_run_columns},
                        ROW_NUMBER() OVER (
                            PARTITION BY track_id
                            ORDER BY analyzed_at DESC, rowid DESC
                        ) AS __scope_rank
                    FROM runs
                    WHERE analyzer_version=? AND analysis_mode=?
                )
                WHERE __scope_rank=1
                ORDER BY track_id
            """
        else:
            selection_sql = f"""
                SELECT {quoted_run_columns}
                FROM runs
                WHERE analyzer_version=? AND analysis_mode=?
                ORDER BY track_id
            """

        destination = sqlite3.connect(temporary)
        destination.execute("PRAGMA journal_mode=DELETE")
        destination.execute("PRAGMA synchronous=FULL")
        destination.execute(_table_schema(source_connection, "tracks"))
        destination.execute(_table_schema(source_connection, "runs"))

        run_insert = (
            f"INSERT INTO runs ({quoted_run_columns}) VALUES ("
            + ",".join("?" for _ in run_columns)
            + ")"
        )
        selected_track_ids: list[str] = []
        selected_paths: dict[str, str | None] = {}
        selected_times: dict[str, str | None] = {}
        cursor = source_connection.execute(selection_sql, (analyzer_version, analysis_mode))
        while True:
            rows = cursor.fetchmany(256)
            if not rows:
                break
            destination.executemany(
                run_insert,
                [tuple(row[name] for name in run_columns) for row in rows],
            )
            for row in rows:
                track_id = str(row["track_id"])
                selected_track_ids.append(track_id)
                selected_paths[track_id] = (
                    str(row["source_path"]) if row["source_path"] is not None else None
                )
                selected_times[track_id] = (
                    str(row["analyzed_at"]) if row["analyzed_at"] is not None else None
                )

        if len(selected_track_ids) != len(set(selected_track_ids)):
            raise RuntimeError("internal scope selection produced duplicate track_id values")

        quoted_track_columns = ", ".join(_quote_identifier(name) for name in track_columns)
        track_insert = (
            f"INSERT INTO tracks ({quoted_track_columns}) VALUES ("
            + ",".join("?" for _ in track_columns)
            + ")"
        )
        copied_tracks = 0
        ordered_track_ids = sorted(selected_track_ids)
        for start in range(0, len(ordered_track_ids), 500):
            chunk = ordered_track_ids[start : start + 500]
            placeholders = ",".join("?" for _ in chunk)
            rows = source_connection.execute(
                f"""
                SELECT {quoted_track_columns}
                FROM tracks
                WHERE track_id IN ({placeholders})
                ORDER BY track_id
                """,
                chunk,
            ).fetchall()
            destination.executemany(
                track_insert,
                [tuple(row[name] for name in track_columns) for row in rows],
            )
            copied_tracks += len(rows)

        if copied_tracks != len(ordered_track_ids):
            raise RuntimeError(
                f"selected {len(ordered_track_ids)} track IDs but copied {copied_tracks} track rows"
            )

        if "last_seen_at" in track_columns:
            destination.executemany(
                "UPDATE tracks SET last_path=?, last_seen_at=? WHERE track_id=?",
                [
                    (selected_paths[track_id], selected_times[track_id], track_id)
                    for track_id in ordered_track_ids
                ],
            )
        else:
            destination.executemany(
                "UPDATE tracks SET last_path=? WHERE track_id=?",
                [(selected_paths[track_id], track_id) for track_id in ordered_track_ids],
            )

        for schema in _index_schemas(source_connection, ("tracks", "runs")):
            destination.execute(schema)

        destination.execute(
            f"""
            CREATE TABLE {_quote_identifier(_SCOPE_META_TABLE)} (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        metadata = {
            "scope_schema_version": "1",
            "created_at": _utc_now_iso(),
            "source_path": str(source),
            "source_fingerprint": source_fingerprint_before,
            "source_fingerprint_policy": "db+nonempty-wal-v1",
            "analyzer_version": analyzer_version,
            "analysis_mode": analysis_mode,
            "duplicate_policy": duplicate_policy,
            "matching_runs": str(matching_runs),
            "duplicate_track_ids": str(duplicate_track_ids),
            "selected_tracks": str(len(ordered_track_ids)),
        }
        destination.executemany(
            f"INSERT INTO {_quote_identifier(_SCOPE_META_TABLE)} (key, value) VALUES (?, ?)",
            sorted(metadata.items()),
        )
        create_database_provenance(
            destination,
            source_fingerprint=source_fingerprint_before,
            schema_version="retrieval-scope-1",
        )
        destination.commit()
        integrity_check = str(destination.execute("PRAGMA integrity_check").fetchone()[0])
        if integrity_check.casefold() != "ok":
            raise RuntimeError(f"scoped catalog integrity_check failed: {integrity_check}")
    except Exception as exc:
        record_database_access(
            target_path=source,
            target_fingerprint=source_fingerprint_before,
            operation="scope-build",
            access_mode="readonly",
            success=False,
            details=f"{type(exc).__name__}: {exc}",
        )
        if destination is not None:
            destination.close()
            destination = None
        if source_connection is not None:
            source_connection.close()
            source_connection = None
        temporary.unlink(missing_ok=True)
        raise
    finally:
        if destination is not None:
            destination.close()
        if source_connection is not None:
            source_connection.close()

    source_fingerprint_after = _source_fingerprint(source)
    source_unchanged = source_fingerprint_after == source_fingerprint_before
    if not source_unchanged:
        temporary.unlink(missing_ok=True)
        record_database_access(
            target_path=source,
            target_fingerprint=source_fingerprint_before,
            operation="scope-build",
            access_mode="readonly",
            success=False,
            details="source fingerprint changed before scoped snapshot publication",
        )
        raise RuntimeError("source history changed while scoped snapshot was being built")

    if output.exists() and not force:
        temporary.unlink(missing_ok=True)
        raise FileExistsError(f"output appeared during build: {output}")
    os.replace(temporary, output)

    output_fingerprint = _source_fingerprint(output)
    source_journal = record_database_access(
        target_path=source,
        target_fingerprint=source_fingerprint_before,
        operation="scope-build",
        access_mode="readonly",
        success=True,
        details=f"derived_scope={output}",
    )
    output_journal = record_database_access(
        target_path=output,
        target_fingerprint=output_fingerprint,
        operation="scope-build",
        access_mode="readwrite",
        success=True,
        details=f"source_fingerprint={source_fingerprint_before}",
    )

    return ScopeBuildReport(
        source=str(source),
        output=str(output),
        source_fingerprint=source_fingerprint_before,
        analyzer_version=analyzer_version,
        analysis_mode=analysis_mode,
        duplicate_policy=duplicate_policy,
        matching_runs=matching_runs,
        duplicate_track_ids=duplicate_track_ids,
        selected_tracks=len(ordered_track_ids),
        integrity_check=integrity_check,
        source_unchanged=source_unchanged,
        journal={
            "source": source_journal.to_dict(),
            "output": output_journal.to_dict(),
        },
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a read-only-source retrieval catalog snapshot from Genre_test history "
            "for one analyzer version/mode scope."
        )
    )
    parser.add_argument("source", type=Path, help="Source history.sqlite3")
    parser.add_argument("output", type=Path, help="Output scoped SQLite path")
    parser.add_argument("--analyzer-version", required=True)
    parser.add_argument("--analysis-mode", required=True)
    parser.add_argument(
        "--duplicate-policy",
        choices=("error", "latest"),
        default="error",
        help="Default error is safest; latest uses analyzed_at,rowid deterministic tie-break.",
    )
    parser.add_argument("--force", action="store_true", help="Atomically replace output if it exists")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = build_history_scope(
            args.source,
            args.output,
            analyzer_version=args.analyzer_version,
            analysis_mode=args.analysis_mode,
            duplicate_policy=args.duplicate_policy,
            force=args.force,
        )
    except (FileNotFoundError, FileExistsError, OSError, RuntimeError, ValueError, sqlite3.Error) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
