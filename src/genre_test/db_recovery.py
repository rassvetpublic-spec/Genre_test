from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import uuid
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from .runtime_meta import default_state_dir, legacy_history_path, project_root

KNOWN_DB_NAMES = {"history.sqlite3", "retrieval.sqlite3"}
SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "$recycle.bin",
    "system volume information",
}
HISTORY_REQUIRED = {"tracks", "runs"}
RETRIEVAL_REQUIRED = {"retrieval_meta", "embedding_models", "embeddings"}


@dataclass(frozen=True)
class DatabaseReport:
    path: str
    kind: str
    size_bytes: int
    mtime_ns: int
    wal_bytes: int
    shm_bytes: int
    fingerprint: str | None
    journal_mode: str | None
    quick_check: str | None
    integrity_check: str | None
    healthy: bool
    score: int
    table_counts: dict[str, int] = field(default_factory=dict)
    run_versions: dict[str, int] = field(default_factory=dict)
    analysis_modes: dict[str, int] = field(default_factory=dict)
    scope_meta: dict[str, str] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RepairReport:
    source: str
    output: str
    source_fingerprint_before: str
    source_fingerprint_after: str
    source_unchanged: bool
    output_kind: str
    output_quick_check: str | None
    output_integrity_check: str | None
    output_size_bytes: int
    actions: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def database_fingerprint(path: Path) -> str:
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"database not found: {path}")

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


def _read_only_connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(
        f"{path.resolve().as_uri()}?mode=ro",
        uri=True,
        timeout=5,
    )
    connection.row_factory = sqlite3.Row
    return connection


def _table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }


def classify_tables(tables: set[str]) -> str:
    if HISTORY_REQUIRED <= tables:
        if "retrieval_history_scope_meta" in tables:
            return "scoped-history"
        return "history"
    if RETRIEVAL_REQUIRED <= tables:
        return "retrieval"
    return "unknown"


def _safe_count(connection: sqlite3.Connection, table: str) -> int:
    quoted = '"' + table.replace('"', '""') + '"'
    return int(connection.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0])


def _score(kind: str, healthy: bool, counts: dict[str, int], size_bytes: int) -> int:
    score = 1_000_000 if healthy else -1_000_000
    score += {
        "history": 30_000,
        "scoped-history": 25_000,
        "retrieval": 20_000,
        "unknown": 0,
    }.get(kind, 0)

    if kind in {"history", "scoped-history"}:
        corpus_rows = counts.get("tracks", 0) + counts.get("runs", 0)
        score += min(corpus_rows * 100, 800_000)
    elif kind == "retrieval":
        score += min(counts.get("embeddings", 0) * 100, 800_000)

    score += min(size_bytes // (1024 * 1024), 50_000)
    return score


def _group_count(
    connection: sqlite3.Connection,
    column: str,
) -> dict[str, int]:
    rows = connection.execute(
        f"SELECT {column}, COUNT(*) FROM runs "
        f"GROUP BY {column} ORDER BY COUNT(*) DESC, {column}"
    ).fetchall()
    return {
        str(row[0] if row[0] is not None else "NULL"): int(row[1])
        for row in rows
    }


def audit_database(path: Path, *, full_integrity: bool = False) -> DatabaseReport:
    path = Path(path).expanduser().resolve()
    try:
        stat = path.stat()
    except OSError as exc:
        return DatabaseReport(
            path=str(path),
            kind="unknown",
            size_bytes=0,
            mtime_ns=0,
            wal_bytes=0,
            shm_bytes=0,
            fingerprint=None,
            journal_mode=None,
            quick_check=None,
            integrity_check=None,
            healthy=False,
            score=-1_000_000,
            error=f"{type(exc).__name__}: {exc}",
        )

    wal = path.with_name(path.name + "-wal")
    shm = path.with_name(path.name + "-shm")
    wal_bytes = wal.stat().st_size if wal.is_file() else 0
    shm_bytes = shm.stat().st_size if shm.is_file() else 0

    fingerprint: str | None = None
    journal_mode: str | None = None
    quick_check: str | None = None
    integrity_check: str | None = None
    table_counts: dict[str, int] = {}
    run_versions: dict[str, int] = {}
    analysis_modes: dict[str, int] = {}
    scope_meta: dict[str, str] = {}
    kind = "unknown"
    error: str | None = None

    try:
        fingerprint = database_fingerprint(path)
        connection = _read_only_connect(path)
        try:
            journal_mode = str(connection.execute("PRAGMA journal_mode").fetchone()[0])
            quick_check = str(connection.execute("PRAGMA quick_check").fetchone()[0])
            tables = _table_names(connection)
            kind = classify_tables(tables)

            interesting = {
                "tracks",
                "runs",
                "file_locations",
                "broad_scores",
                "style_scores",
                "embeddings",
                "embedding_models",
                "search_queries",
            }
            for table in sorted(tables & interesting):
                table_counts[table] = _safe_count(connection, table)

            if "runs" in tables:
                run_columns = {
                    str(row[1])
                    for row in connection.execute("PRAGMA table_info(runs)").fetchall()
                }
                if "analyzer_version" in run_columns:
                    run_versions = _group_count(connection, "analyzer_version")
                if "analysis_mode" in run_columns:
                    analysis_modes = _group_count(connection, "analysis_mode")

            if "retrieval_history_scope_meta" in tables:
                scope_meta = {
                    str(row[0]): str(row[1])
                    for row in connection.execute(
                        "SELECT key, value FROM retrieval_history_scope_meta ORDER BY key"
                    ).fetchall()
                }

            if full_integrity:
                integrity_check = str(
                    connection.execute("PRAGMA integrity_check").fetchone()[0]
                )
        finally:
            connection.close()
    except (OSError, sqlite3.Error, ValueError) as exc:
        error = f"{type(exc).__name__}: {exc}"

    healthy = (
        error is None
        and quick_check == "ok"
        and integrity_check in {None, "ok"}
    )
    return DatabaseReport(
        path=str(path),
        kind=kind,
        size_bytes=stat.st_size,
        mtime_ns=stat.st_mtime_ns,
        wal_bytes=wal_bytes,
        shm_bytes=shm_bytes,
        fingerprint=fingerprint,
        journal_mode=journal_mode,
        quick_check=quick_check,
        integrity_check=integrity_check,
        healthy=healthy,
        score=_score(kind, healthy, table_counts, stat.st_size),
        table_counts=table_counts,
        run_versions=run_versions,
        analysis_modes=analysis_modes,
        scope_meta=scope_meta,
        error=error,
    )


def _looks_like_genre_test_db(path: Path) -> bool:
    name = path.name.casefold()
    if name in KNOWN_DB_NAMES:
        return True
    if path.suffix.casefold() != ".sqlite3":
        return False
    lowered_parts = {part.casefold() for part in path.parts}
    return (
        ".genre_test" in lowered_parts
        or "catalog_scopes" in lowered_parts
        or any("genre_test" in part for part in lowered_parts)
    )


def discover_databases(roots: Iterable[Path]) -> list[Path]:
    found: dict[str, Path] = {}
    for root_value in roots:
        root = Path(root_value).expanduser()
        try:
            root = root.resolve()
        except OSError:
            continue

        if root.is_file():
            if _looks_like_genre_test_db(root):
                found[str(root).casefold()] = root
            continue
        if not root.is_dir():
            continue

        for base, dirs, files in os.walk(root):
            dirs[:] = [
                directory
                for directory in dirs
                if directory.casefold() not in SKIP_DIR_NAMES
            ]
            base_path = Path(base)
            for name in files:
                candidate = base_path / name
                if not _looks_like_genre_test_db(candidate):
                    continue
                try:
                    resolved = candidate.resolve()
                except OSError:
                    continue
                found[str(resolved).casefold()] = resolved

    return sorted(found.values(), key=lambda path: str(path).casefold())


def _portable_sibling_roots(project: Path) -> list[Path]:
    """Find immediate root children that look like portable Genre_test installs."""

    if not project.anchor:
        return []
    anchor = Path(project.anchor)
    if not anchor.is_dir():
        return []

    matches: list[Path] = []
    try:
        for child in anchor.iterdir():
            if not child.is_dir():
                continue
            name = child.name.casefold()
            if "genre_test" in name or "genre-test" in name:
                matches.append(child)
    except OSError:
        return []
    return matches


def default_search_roots() -> list[Path]:
    roots: list[Path] = [Path.cwd()]
    project = project_root()
    roots.extend([project, default_state_dir()])
    roots.extend(_portable_sibling_roots(project))
    legacy = legacy_history_path()
    if legacy is not None:
        roots.append(legacy.parent)

    unique: dict[str, Path] = {}
    for root in roots:
        try:
            resolved = root.expanduser().resolve()
        except OSError:
            continue
        unique[str(resolved).casefold()] = resolved
    return list(unique.values())


def scan_databases(
    roots: Iterable[Path] | None = None,
    *,
    full_integrity: bool = False,
) -> list[DatabaseReport]:
    selected = list(roots) if roots is not None else default_search_roots()
    reports = [
        audit_database(path, full_integrity=full_integrity)
        for path in discover_databases(selected)
    ]
    return sorted(reports, key=lambda report: (-report.score, report.path.casefold()))


def repair_database(
    source: Path,
    output: Path,
    *,
    force: bool = False,
    reindex: bool = True,
    full_integrity: bool = True,
) -> RepairReport:
    source = Path(source).expanduser().resolve()
    output = Path(output).expanduser().resolve()

    if not source.is_file():
        raise FileNotFoundError(f"source database not found: {source}")
    if source == output:
        raise ValueError("output must not overwrite source")
    if output.exists() and not force:
        raise FileExistsError(f"output already exists: {output}")

    source_audit = audit_database(source, full_integrity=True)
    if not source_audit.healthy:
        reason = (
            source_audit.error
            or source_audit.integrity_check
            or source_audit.quick_check
        )
        raise RuntimeError(
            "source failed safe-repair preflight; "
            f"page-level salvage is not attempted: {reason}"
        )

    before = database_fingerprint(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + f".tmp-{uuid.uuid4().hex}")
    actions = ["sqlite-backup"]

    source_connection: sqlite3.Connection | None = None
    destination: sqlite3.Connection | None = None
    try:
        source_connection = _read_only_connect(source)
        destination = sqlite3.connect(temporary)
        source_connection.backup(destination)
        if reindex:
            destination.execute("REINDEX")
            actions.append("reindex")
        destination.commit()

        quick = str(destination.execute("PRAGMA quick_check").fetchone()[0])
        integrity = (
            str(destination.execute("PRAGMA integrity_check").fetchone()[0])
            if full_integrity
            else None
        )
        if quick != "ok" or integrity not in {None, "ok"}:
            raise RuntimeError(
                "repaired copy validation failed: "
                f"quick={quick!r}, integrity={integrity!r}"
            )
    except Exception:
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

    after = database_fingerprint(source)
    if after != before:
        temporary.unlink(missing_ok=True)
        raise RuntimeError("source changed while repair copy was being built")

    temp_audit = audit_database(temporary, full_integrity=full_integrity)
    if not temp_audit.healthy:
        temporary.unlink(missing_ok=True)
        raise RuntimeError("temporary repaired copy failed audit")
    if temp_audit.kind != source_audit.kind:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(
            "database kind changed during repair: "
            f"{source_audit.kind} -> {temp_audit.kind}"
        )

    previous_backup: Path | None = None
    if output.exists():
        if not force:
            temporary.unlink(missing_ok=True)
            raise FileExistsError(f"output appeared during repair: {output}")
        stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        previous_backup = output.with_name(
            output.name + f".pre-repair-{stamp}.bak"
        )
        os.replace(output, previous_backup)
        actions.append(f"destination-backup:{previous_backup}")

    try:
        os.replace(temporary, output)
        output_audit = audit_database(output, full_integrity=full_integrity)
        if not output_audit.healthy:
            raise RuntimeError("published repaired copy failed final audit")
    except Exception:
        output.unlink(missing_ok=True)
        if previous_backup is not None and previous_backup.exists():
            os.replace(previous_backup, output)
        raise

    return RepairReport(
        source=str(source),
        output=str(output),
        source_fingerprint_before=before,
        source_fingerprint_after=after,
        source_unchanged=True,
        output_kind=output_audit.kind,
        output_quick_check=output_audit.quick_check,
        output_integrity_check=output_audit.integrity_check,
        output_size_bytes=output_audit.size_bytes,
        actions=tuple(actions),
    )


def write_scan_reports(
    reports: list[DatabaseReport],
    prefix: Path,
) -> dict[str, Path]:
    prefix = Path(prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = prefix.with_suffix(".json")
    markdown_path = prefix.with_suffix(".md")

    payload = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "candidate_count": len(reports),
        "candidates": [report.to_dict() for report in reports],
    }
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Genre_test database recovery report",
        "",
        f"Candidates: **{len(reports)}**",
        "",
        "| Rank | Kind | Healthy | Score | Size MB | Tracks | Runs | Embeddings | Path |",
        "|---:|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for rank, report in enumerate(reports, 1):
        counts = report.table_counts
        escaped_path = report.path.replace("|", "\\|")
        lines.append(
            f"| {rank} | {report.kind} | {report.healthy} | {report.score} | "
            f"{report.size_bytes / 1024**2:.2f} | {counts.get('tracks', 0)} | "
            f"{counts.get('runs', 0)} | {counts.get('embeddings', 0)} | "
            f"`{escaped_path}` |"
        )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def write_repair_report(report: RepairReport, prefix: Path) -> dict[str, Path]:
    prefix = Path(prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = prefix.with_suffix(".json")
    markdown_path = prefix.with_suffix(".md")

    json_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Genre_test database repair report",
        "",
        f"- Source: `{report.source}`",
        f"- Output: `{report.output}`",
        f"- Source unchanged: **{report.source_unchanged}**",
        f"- Output kind: `{report.output_kind}`",
        f"- Quick check: `{report.output_quick_check}`",
        f"- Integrity check: `{report.output_integrity_check}`",
        f"- Output bytes: {report.output_size_bytes}",
        f"- Actions: {', '.join(report.actions)}",
    ]
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Genre_test SQLite discovery, audit and safe repair"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    scan = commands.add_parser("scan", help="discover and rank Genre_test databases")
    scan.add_argument("roots", nargs="*", type=Path)
    scan.add_argument("--full-integrity", action="store_true")
    scan.add_argument("--out-prefix", type=Path)

    audit = commands.add_parser("audit", help="audit one database read-only")
    audit.add_argument("path", type=Path)
    audit.add_argument("--full-integrity", action="store_true")

    repair = commands.add_parser("repair", help="create a validated repaired copy")
    repair.add_argument("source", type=Path)
    repair.add_argument("output", type=Path)
    repair.add_argument("--force", action="store_true")
    repair.add_argument("--no-reindex", action="store_true")
    repair.add_argument("--quick-only", action="store_true")
    repair.add_argument("--out-prefix", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "scan":
            roots = args.roots or default_search_roots()
            reports = scan_databases(roots, full_integrity=args.full_integrity)
            payload: dict[str, object] = {
                "roots": [str(Path(root)) for root in roots],
                "candidate_count": len(reports),
                "candidates": [report.to_dict() for report in reports],
            }
            if args.out_prefix:
                payload["files"] = {
                    key: str(value)
                    for key, value in write_scan_reports(
                        reports,
                        args.out_prefix,
                    ).items()
                }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        if args.command == "audit":
            report = audit_database(args.path, full_integrity=args.full_integrity)
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
            return 0 if report.healthy else 2

        if args.command == "repair":
            report = repair_database(
                args.source,
                args.output,
                force=args.force,
                reindex=not args.no_reindex,
                full_integrity=not args.quick_only,
            )
            payload = report.to_dict()
            if args.out_prefix:
                payload["files"] = {
                    key: str(value)
                    for key, value in write_repair_report(
                        report,
                        args.out_prefix,
                    ).items()
                }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        raise RuntimeError(f"unknown command: {args.command}")
    except (
        FileNotFoundError,
        FileExistsError,
        OSError,
        RuntimeError,
        ValueError,
        sqlite3.Error,
    ) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
