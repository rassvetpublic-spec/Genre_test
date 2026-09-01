from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from genre_test.db_access_journal import (
    access_summary,
    current_build_identity,
    read_database_provenance,
    record_database_access,
)
from genre_test.db_recovery import database_fingerprint
from genre_test.db_recovery_provenance import (
    audit_database,
    repair_database,
    scan_databases,
)


def _make_history(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE tracks(
                track_id TEXT PRIMARY KEY,
                last_path TEXT
            );
            CREATE TABLE runs(
                run_id TEXT PRIMARY KEY,
                track_id TEXT,
                analyzer_version TEXT,
                analysis_mode TEXT,
                source_path TEXT
            );
            """
        )
        connection.execute(
            "INSERT INTO tracks(track_id, last_path) VALUES(?, ?)",
            ("sha256:" + "1" * 64, "D:/Музыка/тест.wav"),
        )
        connection.execute(
            """
            INSERT INTO runs(
                run_id, track_id, analyzer_version, analysis_mode, source_path
            ) VALUES(?, ?, ?, ?, ?)
            """,
            (
                "run-1",
                "sha256:" + "1" * 64,
                "0.4.0",
                "auto",
                "D:/Музыка/тест.wav",
            ),
        )
    return path


def test_read_only_audit_journals_without_mutating_source(
    tmp_path: Path,
    monkeypatch,
) -> None:
    state = tmp_path / "state"
    monkeypatch.setenv("GENRE_TEST_DATA_DIR", str(state))
    source = _make_history(tmp_path / "Юникод" / "history.sqlite3")
    before = database_fingerprint(source)

    report = audit_database(source, full_integrity=True)

    assert report["healthy"] is True
    assert report["target_unchanged"] is True
    assert database_fingerprint(source) == before
    assert report["journal"]["recorded"] is True
    assert report["access_provenance"]["last_read"] is not None
    assert report["database_provenance"] == {"status": "unknown/legacy"}
    assert (state / "database_access.sqlite3").is_file()


def test_journal_failure_is_explicit_but_does_not_block_audit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    blocked_state = tmp_path / "not-a-directory"
    blocked_state.write_text("occupied", encoding="utf-8")
    monkeypatch.setenv("GENRE_TEST_DATA_DIR", str(blocked_state))
    source = _make_history(tmp_path / "history.sqlite3")
    before = database_fingerprint(source)

    report = audit_database(source)

    assert report["healthy"] is True
    assert report["target_unchanged"] is True
    assert database_fingerprint(source) == before
    assert report["journal"]["recorded"] is False
    assert report["journal"]["error"]


def test_scan_excludes_access_journal_and_direct_self_audit_is_rejected(
    tmp_path: Path,
    monkeypatch,
) -> None:
    state = tmp_path / ".genre_test"
    monkeypatch.setenv("GENRE_TEST_DATA_DIR", str(state))
    source = _make_history(tmp_path / "history.sqlite3")

    first = audit_database(source)
    journal = Path(first["journal"]["journal_path"])
    journal_before = database_fingerprint(journal)

    assert scan_databases([state]) == []
    assert database_fingerprint(journal) == journal_before
    with pytest.raises(ValueError, match="cannot audit itself"):
        audit_database(journal)
    assert database_fingerprint(journal) == journal_before


def test_repair_writes_provenance_only_to_derived_copy(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GENRE_TEST_DATA_DIR", str(tmp_path / "state"))
    source = _make_history(tmp_path / "source" / "history.sqlite3")
    output = tmp_path / "derived" / "history.sqlite3"
    source_before = database_fingerprint(source)

    report = repair_database(source, output)

    assert report["source_unchanged"] is True
    assert database_fingerprint(source) == source_before
    assert report["output"] == str(output.resolve())
    assert "embedded-provenance" in report["actions"]
    assert report["output_database_provenance"]["source_fingerprint"] == source_before
    assert report["output_database_provenance"]["database_uuid"]
    assert report["output_database_provenance"]["build_fingerprint"]
    assert report["output_access_provenance"]["last_write"] is not None

    with sqlite3.connect(f"{source.as_uri()}?mode=ro", uri=True) as connection:
        assert read_database_provenance(connection) == {"status": "unknown/legacy"}
    with sqlite3.connect(f"{output.as_uri()}?mode=ro", uri=True) as connection:
        metadata = read_database_provenance(connection)
    assert metadata["status"] == "known"
    assert metadata["source_fingerprint"] == source_before


def test_provenance_failure_does_not_publish_or_displace_force_destination(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GENRE_TEST_DATA_DIR", str(tmp_path / "state"))
    source = _make_history(tmp_path / "source" / "history.sqlite3")
    with sqlite3.connect(source) as connection:
        connection.execute(
            "CREATE TABLE genre_test_database_provenance(broken TEXT NOT NULL)"
        )
    output = _make_history(tmp_path / "existing" / "history.sqlite3")
    source_before = database_fingerprint(source)
    output_before = database_fingerprint(output)

    with pytest.raises(sqlite3.Error):
        repair_database(source, output, force=True)

    assert database_fingerprint(source) == source_before
    assert database_fingerprint(output) == output_before
    assert not list(output.parent.glob(output.name + ".pre-repair-*.bak"))
    assert not list(output.parent.glob(output.name + ".provenance-stage-*"))


def test_access_summary_tracks_operation_families(tmp_path: Path) -> None:
    journal = tmp_path / "journal.sqlite3"
    target = tmp_path / "history.sqlite3"
    fingerprint = "f" * 64
    identity = current_build_identity()

    for operation, mode, stamp in (
        ("read", "readonly", "2026-09-01T10:00:00Z"),
        ("scope-build", "readwrite", "2026-09-01T10:01:00Z"),
        ("repair", "readwrite", "2026-09-01T10:02:00Z"),
        ("integrity-check", "readonly", "2026-09-01T10:03:00Z"),
    ):
        result = record_database_access(
            target_path=target,
            target_fingerprint=fingerprint,
            operation=operation,
            access_mode=mode,
            success=True,
            journal_path=journal,
            build_identity=identity,
            event_utc=stamp,
        )
        assert result.recorded is True

    summary = access_summary(
        target_fingerprint=fingerprint,
        journal_path=journal,
    )

    assert summary.last_read == "2026-09-01T10:03:00Z"
    assert summary.last_write == "2026-09-01T10:02:00Z"
    assert summary.last_repair == "2026-09-01T10:02:00Z"
    assert summary.last_scope_build == "2026-09-01T10:01:00Z"
    assert summary.last_integrity_check == "2026-09-01T10:03:00Z"
    assert summary.last_accessing_build
    assert summary.last_accessing_runner


def test_build_fingerprint_excludes_process_specific_identity() -> None:
    first = current_build_identity()
    second = current_build_identity()

    assert first.build_fingerprint == second.build_fingerprint
    assert first.app_version == second.app_version
    assert first.build_channel == second.build_channel
