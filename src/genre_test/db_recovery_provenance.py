from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import db_recovery as core
from .db_access_journal import (
    access_summary,
    create_database_provenance,
    default_journal_path,
    read_database_provenance,
    record_database_access,
)


def _readonly_provenance(path: Path) -> dict[str, str]:
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        return {"status": "unknown/legacy"}
    try:
        with sqlite3.connect(
            f"{path.as_uri()}?mode=ro",
            uri=True,
            timeout=5,
        ) as connection:
            return read_database_provenance(connection)
    except sqlite3.Error:
        return {"status": "unknown/legacy"}


def _is_access_journal(path: Path) -> bool:
    candidate = Path(path).expanduser().resolve(strict=False)
    journal = default_journal_path().expanduser().resolve(strict=False)
    return candidate == journal


def audit_database(
    path: Path,
    *,
    full_integrity: bool = False,
    operation: str = "audit",
) -> dict[str, Any]:
    """Audit through the stable core and add external provenance without target mutation."""

    path = Path(path).expanduser().resolve()
    if _is_access_journal(path):
        raise ValueError("database access journal cannot audit itself")

    before: str | None = None
    after: str | None = None
    try:
        if path.is_file():
            before = core.database_fingerprint(path)
    except (OSError, ValueError):
        before = None

    report = core.audit_database(path, full_integrity=full_integrity)

    try:
        if path.is_file():
            after = core.database_fingerprint(path)
    except (OSError, ValueError):
        after = None

    target_unchanged = before == after if before is not None and after is not None else None
    journal_result = record_database_access(
        target_path=path,
        target_fingerprint=report.fingerprint or after or before,
        operation=operation,
        access_mode="readonly",
        success=report.error is None and target_unchanged is not False,
        details=(
            report.error
            or (
                f"quick_check={report.quick_check}; "
                f"integrity_check={report.integrity_check}; kind={report.kind}"
            )
        ),
    )
    summary_key = report.fingerprint or after or before
    summary = access_summary(target_fingerprint=summary_key) if summary_key else None

    payload = report.to_dict()
    payload.update(
        {
            "target_fingerprint_before": before,
            "target_fingerprint_after": after,
            "target_unchanged": target_unchanged,
            "database_provenance": _readonly_provenance(path),
            "access_provenance": summary.to_dict() if summary else {},
            "journal": journal_result.to_dict(),
        }
    )
    return payload


def scan_databases(
    roots: list[Path] | None = None,
    *,
    full_integrity: bool = False,
) -> list[dict[str, Any]]:
    selected = list(roots) if roots is not None else core.default_search_roots()
    candidates = [
        path
        for path in core.discover_databases(selected)
        if not _is_access_journal(path)
    ]
    reports = [
        audit_database(path, full_integrity=full_integrity, operation="scan")
        for path in candidates
    ]
    return sorted(
        reports,
        key=lambda report: (-int(report["score"]), str(report["path"]).casefold()),
    )


def _write_output_provenance(
    output: Path,
    *,
    source_fingerprint: str,
) -> dict[str, str]:
    with sqlite3.connect(output) as connection:
        user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        payload = create_database_provenance(
            connection,
            source_fingerprint=source_fingerprint,
            schema_version=str(user_version),
        )
        connection.commit()
    return payload


def repair_database(
    source: Path,
    output: Path,
    *,
    force: bool = False,
    reindex: bool = True,
    full_integrity: bool = True,
) -> dict[str, Any]:
    source = Path(source).expanduser().resolve()
    output = Path(output).expanduser().resolve()
    if source == output:
        raise ValueError("output must not overwrite source")
    if output.exists() and not force:
        raise FileExistsError(f"output already exists: {output}")
    if _is_access_journal(source) or _is_access_journal(output):
        raise ValueError("database access journal cannot be a repair source or output")

    source_before = core.database_fingerprint(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = output.with_name(output.name + f".provenance-stage-{uuid.uuid4().hex}")
    previous_backup: Path | None = None
    output_metadata: dict[str, str] = {}
    actions: list[str] = []

    try:
        core_report = core.repair_database(
            source,
            staging,
            force=False,
            reindex=reindex,
            full_integrity=full_integrity,
        )
        actions.extend(core_report.actions)

        output_metadata = _write_output_provenance(
            staging,
            source_fingerprint=source_before,
        )
        actions.append("embedded-provenance")

        staging_audit = core.audit_database(staging, full_integrity=full_integrity)
        if not staging_audit.healthy:
            raise RuntimeError("provenance-enriched staged repair failed final audit")

        source_after = core.database_fingerprint(source)
        if source_after != source_before:
            raise RuntimeError("source changed while provenance-aware repair was running")

        if output.exists():
            if not force:
                raise FileExistsError(f"output appeared during repair: {output}")
            stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            previous_backup = output.with_name(
                output.name + f".pre-repair-{stamp}.bak"
            )
            os.replace(output, previous_backup)
            actions.append(f"destination-backup:{previous_backup}")

        try:
            os.replace(staging, output)
            output_audit = core.audit_database(output, full_integrity=full_integrity)
            if not output_audit.healthy:
                raise RuntimeError("published provenance-enriched repair failed final audit")
        except Exception:
            output.unlink(missing_ok=True)
            if previous_backup is not None and previous_backup.exists():
                os.replace(previous_backup, output)
            raise
    except Exception as exc:
        staging.unlink(missing_ok=True)
        record_database_access(
            target_path=source,
            target_fingerprint=source_before,
            operation="repair",
            access_mode="readonly",
            success=False,
            details=f"{type(exc).__name__}: {exc}",
        )
        raise

    source_journal = record_database_access(
        target_path=source,
        target_fingerprint=source_before,
        operation="repair",
        access_mode="readonly",
        success=True,
        details=f"derived_copy={output}",
    )
    output_journal = record_database_access(
        target_path=output,
        target_fingerprint=output_audit.fingerprint,
        operation="repair",
        access_mode="readwrite",
        success=True,
        details=f"source_fingerprint={source_before}",
    )
    source_access = access_summary(target_fingerprint=source_before)
    output_access = (
        access_summary(target_fingerprint=output_audit.fingerprint)
        if output_audit.fingerprint
        else None
    )

    payload = core_report.to_dict()
    payload.update(
        {
            "output": str(output),
            "actions": actions,
            "source_fingerprint_after": source_after,
            "source_unchanged": source_after == source_before,
            "output_fingerprint": output_audit.fingerprint,
            "output_quick_check": output_audit.quick_check,
            "output_integrity_check": output_audit.integrity_check,
            "output_size_bytes": output_audit.size_bytes,
            "output_database_provenance": output_metadata,
            "source_access_provenance": source_access.to_dict(),
            "output_access_provenance": output_access.to_dict() if output_access else {},
            "journal": {
                "source": source_journal.to_dict(),
                "output": output_journal.to_dict(),
            },
        }
    )
    return payload


def write_scan_reports(reports: list[dict[str, Any]], prefix: Path) -> dict[str, Path]:
    prefix = Path(prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = prefix.with_suffix(".json")
    markdown_path = prefix.with_suffix(".md")
    payload = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "candidate_count": len(reports),
        "candidates": reports,
    }
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Genre_test database recovery + provenance report",
        "",
        f"Candidates: **{len(reports)}**",
        "",
        "| Rank | Kind | Healthy | Last read | Last write | Last repair | Build | Path |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for rank, report in enumerate(reports, 1):
        access = report.get("access_provenance") or {}
        escaped_path = str(report["path"]).replace("|", "\\|")
        lines.append(
            f"| {rank} | {report['kind']} | {report['healthy']} | "
            f"{access.get('last_read') or '-'} | {access.get('last_write') or '-'} | "
            f"{access.get('last_repair') or '-'} | "
            f"{access.get('last_accessing_build') or '-'} | `{escaped_path}` |"
        )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def write_repair_report(report: dict[str, Any], prefix: Path) -> dict[str, Path]:
    prefix = Path(prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = prefix.with_suffix(".json")
    markdown_path = prefix.with_suffix(".md")
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    source_access = report.get("source_access_provenance") or {}
    output_access = report.get("output_access_provenance") or {}
    lines = [
        "# Genre_test database repair + provenance report",
        "",
        f"- Source: `{report['source']}`",
        f"- Output: `{report['output']}`",
        f"- Source unchanged: **{report['source_unchanged']}**",
        f"- Output kind: `{report['output_kind']}`",
        f"- Quick check: `{report['output_quick_check']}`",
        f"- Integrity check: `{report['output_integrity_check']}`",
        f"- Last source repair: `{source_access.get('last_repair') or 'unknown'}`",
        f"- Last output write: `{output_access.get('last_write') or 'unknown'}`",
        f"- Output build: `{output_access.get('last_accessing_build') or 'unknown'}`",
    ]
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Genre_test SQLite recovery with external access provenance"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    scan = commands.add_parser("scan", help="discover, rank and journal Genre_test databases")
    scan.add_argument("roots", nargs="*", type=Path)
    scan.add_argument("--full-integrity", action="store_true")
    scan.add_argument("--out-prefix", type=Path)

    audit = commands.add_parser("audit", help="audit one database read-only and journal it")
    audit.add_argument("path", type=Path)
    audit.add_argument("--full-integrity", action="store_true")

    repair = commands.add_parser("repair", help="create a provenance-enriched repaired copy")
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
            roots = args.roots or core.default_search_roots()
            reports = scan_databases(roots, full_integrity=args.full_integrity)
            payload: dict[str, Any] = {
                "roots": [str(Path(root)) for root in roots],
                "candidate_count": len(reports),
                "candidates": reports,
            }
            if args.out_prefix:
                payload["files"] = {
                    key: str(value)
                    for key, value in write_scan_reports(reports, args.out_prefix).items()
                }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        if args.command == "audit":
            report = audit_database(args.path, full_integrity=args.full_integrity)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if report["healthy"] else 2

        if args.command == "repair":
            report = repair_database(
                args.source,
                args.output,
                force=args.force,
                reindex=not args.no_reindex,
                full_integrity=not args.quick_only,
            )
            if args.out_prefix:
                report["files"] = {
                    key: str(value)
                    for key, value in write_repair_report(report, args.out_prefix).items()
                }
            print(json.dumps(report, ensure_ascii=False, indent=2))
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
