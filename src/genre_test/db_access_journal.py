from __future__ import annotations

import getpass
import hashlib
import json
import os
import platform
import socket
import sqlite3
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import __version__
from .runtime_meta import current_git_commit, default_state_dir

JOURNAL_SCHEMA_VERSION = 1
PROVENANCE_SCHEMA_VERSION = 1
ALLOWED_OPERATIONS = {
    "scan",
    "audit",
    "read",
    "write",
    "scope-build",
    "repair",
    "salvage",
    "integrity-check",
}
ALLOWED_ACCESS_MODES = {"readonly", "readwrite"}
ALLOWED_BUILD_CHANNELS = {"dev", "portable", "release"}


@dataclass(frozen=True)
class BuildIdentity:
    app_version: str
    git_commit: str | None
    build_fingerprint: str
    build_channel: str
    process_id: int
    host: str
    os_user: str
    python_runtime: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class JournalWriteResult:
    recorded: bool
    journal_path: str
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AccessSummary:
    last_read: str | None = None
    last_write: str | None = None
    last_repair: str | None = None
    last_scope_build: str | None = None
    last_integrity_check: str | None = None
    last_accessing_build: str | None = None
    last_accessing_runner: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def default_journal_path() -> Path:
    return default_state_dir() / "database_access.sqlite3"


def _build_channel() -> str:
    value = os.environ.get("GENRE_TEST_BUILD_CHANNEL", "dev").strip().lower()
    return value if value in ALLOWED_BUILD_CHANNELS else "dev"


def current_build_identity() -> BuildIdentity:
    commit = current_git_commit()
    channel = _build_channel()
    stable = {
        "schema": "genre-test-build-fingerprint-v1",
        "app_version": __version__,
        "git_commit": commit or "unknown",
        "build_channel": channel,
    }
    encoded = json.dumps(
        stable,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    fingerprint = hashlib.sha256(encoded).hexdigest()
    return BuildIdentity(
        app_version=__version__,
        git_commit=commit,
        build_fingerprint=fingerprint,
        build_channel=channel,
        process_id=os.getpid(),
        host=socket.gethostname() or "unknown",
        os_user=getpass.getuser() or "unknown",
        python_runtime=f"{platform.python_implementation()} {platform.python_version()}",
    )


def path_fallback_fingerprint(path: Path) -> str:
    """Stable non-content key used only when the target content cannot be fingerprinted."""

    resolved = str(Path(path).expanduser().resolve(strict=False))
    digest = hashlib.sha256(resolved.encode("utf-8", errors="surrogatepass")).hexdigest()
    return f"path:{digest}"


def _compact_details(details: str | None) -> str | None:
    if details is None:
        return None
    normalized = " ".join(str(details).split())
    return normalized[:512] or None


def _initialize_journal(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS journal_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS access_events (
            event_id TEXT PRIMARY KEY,
            target_fingerprint TEXT NOT NULL,
            target_path TEXT NOT NULL,
            event_utc TEXT NOT NULL,
            operation TEXT NOT NULL,
            access_mode TEXT NOT NULL,
            app_version TEXT NOT NULL,
            git_commit TEXT,
            build_fingerprint TEXT NOT NULL,
            build_channel TEXT NOT NULL,
            process_id INTEGER NOT NULL,
            host TEXT NOT NULL,
            os_user TEXT NOT NULL,
            python_runtime TEXT NOT NULL,
            success INTEGER NOT NULL,
            details TEXT
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_access_events_target_time "
        "ON access_events(target_fingerprint, event_utc DESC)"
    )
    connection.execute(
        "INSERT OR REPLACE INTO journal_meta(key, value) VALUES (?, ?)",
        ("schema_version", str(JOURNAL_SCHEMA_VERSION)),
    )


def record_database_access(
    *,
    target_path: Path,
    target_fingerprint: str | None,
    operation: str,
    access_mode: str,
    success: bool,
    details: str | None = None,
    journal_path: Path | None = None,
    build_identity: BuildIdentity | None = None,
    event_utc: str | None = None,
) -> JournalWriteResult:
    """Best-effort external journal write; never mutates the audited target database."""

    if operation not in ALLOWED_OPERATIONS:
        raise ValueError(f"unsupported database access operation: {operation}")
    if access_mode not in ALLOWED_ACCESS_MODES:
        raise ValueError(f"unsupported database access mode: {access_mode}")

    path = Path(target_path).expanduser().resolve(strict=False)
    journal = Path(journal_path or default_journal_path()).expanduser().resolve(strict=False)
    identity = build_identity or current_build_identity()
    fingerprint = target_fingerprint or path_fallback_fingerprint(path)
    try:
        journal.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(journal) as connection:
            _initialize_journal(connection)
            connection.execute(
                """
                INSERT INTO access_events (
                    event_id,
                    target_fingerprint,
                    target_path,
                    event_utc,
                    operation,
                    access_mode,
                    app_version,
                    git_commit,
                    build_fingerprint,
                    build_channel,
                    process_id,
                    host,
                    os_user,
                    python_runtime,
                    success,
                    details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    fingerprint,
                    str(path),
                    event_utc or utc_now_iso(),
                    operation,
                    access_mode,
                    identity.app_version,
                    identity.git_commit,
                    identity.build_fingerprint,
                    identity.build_channel,
                    identity.process_id,
                    identity.host,
                    identity.os_user,
                    identity.python_runtime,
                    int(bool(success)),
                    _compact_details(details),
                ),
            )
            connection.commit()
    except (OSError, sqlite3.Error) as exc:
        return JournalWriteResult(
            recorded=False,
            journal_path=str(journal),
            error=f"{type(exc).__name__}: {exc}",
        )
    return JournalWriteResult(recorded=True, journal_path=str(journal))


def access_summary(
    *,
    target_fingerprint: str,
    journal_path: Path | None = None,
) -> AccessSummary:
    journal = Path(journal_path or default_journal_path()).expanduser().resolve(strict=False)
    if not journal.is_file():
        return AccessSummary()
    try:
        with sqlite3.connect(
            f"{journal.as_uri()}?mode=ro",
            uri=True,
            timeout=5,
        ) as connection:
            rows = connection.execute(
                """
                SELECT event_utc, operation, access_mode, build_fingerprint,
                       git_commit, host, process_id
                FROM access_events
                WHERE target_fingerprint = ? AND success = 1
                ORDER BY event_utc DESC, rowid DESC
                """,
                (target_fingerprint,),
            ).fetchall()
    except (OSError, sqlite3.Error):
        return AccessSummary()

    last_read: str | None = None
    last_write: str | None = None
    last_repair: str | None = None
    last_scope_build: str | None = None
    last_integrity_check: str | None = None
    last_build: str | None = None
    last_runner: str | None = None
    for event_utc, operation, access_mode, build_fingerprint, git_commit, host, pid in rows:
        stamp = str(event_utc)
        if last_read is None and access_mode == "readonly":
            last_read = stamp
        if last_write is None and access_mode == "readwrite":
            last_write = stamp
        if last_repair is None and operation == "repair":
            last_repair = stamp
        if last_scope_build is None and operation == "scope-build":
            last_scope_build = stamp
        if last_integrity_check is None and operation in {"audit", "integrity-check"}:
            last_integrity_check = stamp
        if last_build is None:
            last_build = str(git_commit or build_fingerprint)
            last_runner = f"{host}:pid={pid}"
        if all(
            value is not None
            for value in (
                last_read,
                last_write,
                last_repair,
                last_scope_build,
                last_integrity_check,
                last_build,
                last_runner,
            )
        ):
            break
    return AccessSummary(
        last_read=last_read,
        last_write=last_write,
        last_repair=last_repair,
        last_scope_build=last_scope_build,
        last_integrity_check=last_integrity_check,
        last_accessing_build=last_build,
        last_accessing_runner=last_runner,
    )


def create_database_provenance(
    connection: sqlite3.Connection,
    *,
    source_fingerprint: str | None = None,
    schema_version: str | None = None,
    build_identity: BuildIdentity | None = None,
    created_at: str | None = None,
) -> dict[str, str]:
    """Write provenance to a newly created/derived DB, never to an audited source."""

    identity = build_identity or current_build_identity()
    payload = {
        "database_uuid": str(uuid.uuid4()),
        "provenance_schema_version": str(PROVENANCE_SCHEMA_VERSION),
        "db_schema_version": schema_version or "unknown",
        "app_version": identity.app_version,
        "build_commit_sha": identity.git_commit or "unknown",
        "build_fingerprint": identity.build_fingerprint,
        "build_channel": identity.build_channel,
        "created_at": created_at or utc_now_iso(),
        "source_fingerprint": source_fingerprint or "none",
    }
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS genre_test_database_provenance (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    connection.executemany(
        "INSERT OR REPLACE INTO genre_test_database_provenance(key, value) VALUES (?, ?)",
        sorted(payload.items()),
    )
    return payload


def read_database_provenance(connection: sqlite3.Connection) -> dict[str, str]:
    try:
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "genre_test_database_provenance" not in tables:
            return {"status": "unknown/legacy"}
        rows = connection.execute(
            "SELECT key, value FROM genre_test_database_provenance ORDER BY key"
        ).fetchall()
    except sqlite3.Error:
        return {"status": "unknown/legacy"}
    payload = {str(key): str(value) for key, value in rows}
    payload["status"] = "known" if payload else "unknown/legacy"
    return payload


def journal_health(journal_path: Path | None = None) -> dict[str, Any]:
    journal = Path(journal_path or default_journal_path()).expanduser().resolve(strict=False)
    if not journal.exists():
        return {"path": str(journal), "status": "not-created"}
    try:
        with sqlite3.connect(
            f"{journal.as_uri()}?mode=ro",
            uri=True,
            timeout=5,
        ) as connection:
            quick_check = str(connection.execute("PRAGMA quick_check").fetchone()[0])
            schema_version = connection.execute(
                "SELECT value FROM journal_meta WHERE key='schema_version'"
            ).fetchone()
    except (OSError, sqlite3.Error) as exc:
        return {
            "path": str(journal),
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {
        "path": str(journal),
        "status": "ok" if quick_check == "ok" else "error",
        "quick_check": quick_check,
        "schema_version": str(schema_version[0]) if schema_version else "unknown",
        "python": sys.version.split()[0],
    }
