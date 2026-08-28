from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from genre_test.db_recovery import (
    audit_database,
    database_fingerprint,
    discover_databases,
    main,
    repair_database,
    scan_databases,
    write_repair_report,
    write_scan_reports,
)


def make_history(path: Path, *, tracks: int, scoped: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE tracks(track_id TEXT PRIMARY KEY, last_path TEXT);
        CREATE TABLE runs(
            run_id TEXT PRIMARY KEY,
            track_id TEXT,
            analyzer_version TEXT,
            analysis_mode TEXT,
            source_path TEXT
        );
        CREATE TABLE file_locations(path TEXT PRIMARY KEY, track_id TEXT);
        """
    )
    if scoped:
        connection.execute(
            """
            CREATE TABLE retrieval_history_scope_meta(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        connection.executemany(
            "INSERT INTO retrieval_history_scope_meta VALUES(?, ?)",
            [
                ("selected_tracks", str(tracks)),
                ("analyzer_version", "0.4.0"),
            ],
        )

    for index in range(tracks):
        track_id = f"sha256:{index:064x}"
        audio = f"D:/! Музыка/Beyoncé/{index}.mp3"
        connection.execute("INSERT INTO tracks VALUES(?, ?)", (track_id, audio))
        connection.execute(
            "INSERT INTO runs VALUES(?, ?, ?, ?, ?)",
            (f"run-{index}", track_id, "0.4.0", "auto", audio),
        )
        connection.execute(
            "INSERT INTO file_locations VALUES(?, ?)",
            (audio, track_id),
        )

    connection.commit()
    connection.close()
    return path


def make_retrieval(path: Path, *, embeddings: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE retrieval_meta(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE embedding_models(fingerprint TEXT PRIMARY KEY);
        CREATE TABLE embeddings(cache_key TEXT PRIMARY KEY, track_id TEXT);
        CREATE TABLE search_queries(query_id INTEGER PRIMARY KEY);
        """
    )
    for index in range(embeddings):
        connection.execute(
            "INSERT INTO embeddings VALUES(?, ?)",
            (f"key-{index}", f"track-{index}"),
        )
    connection.commit()
    connection.close()
    return path


def test_discovery_classification_and_sidecars(tmp_path: Path) -> None:
    root = tmp_path / "Genre_test_lab"
    history = make_history(root / ".genre_test" / "history.sqlite3", tracks=12)
    scoped = make_history(
        root / ".genre_test" / "catalog_scopes" / "v04_auto.sqlite3",
        tracks=8,
        scoped=True,
    )
    retrieval = make_retrieval(
        root / ".genre_test" / "retrieval.sqlite3",
        embeddings=4,
    )
    history.with_name(history.name + "-wal").write_bytes(b"")

    discovered = discover_databases([root])

    assert history in discovered
    assert scoped in discovered
    assert retrieval in discovered
    assert all(not str(path).endswith("-wal") for path in discovered)

    reports = scan_databases([root], full_integrity=True)
    kinds = {Path(report.path).name: report.kind for report in reports}

    assert kinds["history.sqlite3"] == "history"
    assert kinds["v04_auto.sqlite3"] == "scoped-history"
    assert kinds["retrieval.sqlite3"] == "retrieval"
    assert all(report.healthy for report in reports)


def test_ranking_prefers_larger_valid_corpus(tmp_path: Path) -> None:
    root = tmp_path / "Genre_test_rank"
    make_history(root / "tiny" / "history.sqlite3", tracks=2)
    make_history(
        root / "large" / ".genre_test" / "catalog_scopes" / "v04.sqlite3",
        tracks=100,
        scoped=True,
    )
    make_retrieval(root / "retrieval.sqlite3", embeddings=10)

    reports = scan_databases([root], full_integrity=True)

    assert reports[0].kind == "scoped-history"
    assert reports[0].table_counts["tracks"] == 100


def test_audit_reports_versions_modes_and_unicode(tmp_path: Path) -> None:
    history = make_history(
        tmp_path / "Genre_test_Юникод" / ".genre_test" / "history.sqlite3",
        tracks=3,
    )

    report = audit_database(history, full_integrity=True)

    assert report.healthy is True
    assert report.quick_check == "ok"
    assert report.integrity_check == "ok"
    assert report.run_versions == {"0.4.0": 3}
    assert report.analysis_modes == {"auto": 3}


def test_safe_repair_preserves_source_and_rows(tmp_path: Path) -> None:
    source = make_history(
        tmp_path / "Genre_test_source" / ".genre_test" / "history.sqlite3",
        tracks=20,
    )
    output = tmp_path / "repaired" / "history.sqlite3"
    before = database_fingerprint(source)

    result = repair_database(source, output)

    assert result.source_unchanged is True
    assert database_fingerprint(source) == before
    assert output.is_file()
    repaired = audit_database(output, full_integrity=True)
    assert repaired.healthy is True
    assert repaired.kind == "history"
    assert repaired.table_counts["tracks"] == 20
    assert repaired.table_counts["runs"] == 20
    assert result.actions == ("sqlite-backup", "reindex")


def test_collision_fails_without_force_and_force_backs_up_destination(
    tmp_path: Path,
) -> None:
    source = make_history(
        tmp_path / "Genre_test_source" / ".genre_test" / "history.sqlite3",
        tracks=5,
    )
    output = make_history(
        tmp_path / "repair" / "history.sqlite3",
        tracks=1,
    )

    with pytest.raises(FileExistsError):
        repair_database(source, output)

    result = repair_database(source, output, force=True)

    assert audit_database(output, full_integrity=True).table_counts["tracks"] == 5
    backup_actions = [
        action
        for action in result.actions
        if action.startswith("destination-backup:")
    ]
    assert len(backup_actions) == 1
    backup_path = Path(backup_actions[0].split(":", 1)[1])
    assert backup_path.exists()
    assert audit_database(backup_path, full_integrity=True).table_counts["tracks"] == 1


def test_corrupt_source_fails_closed_without_output(tmp_path: Path) -> None:
    source = tmp_path / "Genre_test_broken" / "history.sqlite3"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"this is not sqlite")
    output = tmp_path / "repair" / "history.sqlite3"

    report = audit_database(source, full_integrity=True)
    assert report.healthy is False

    with pytest.raises(RuntimeError, match="page-level salvage is not attempted"):
        repair_database(source, output)

    assert not output.exists()


def test_missing_source_never_creates_database(tmp_path: Path) -> None:
    missing = tmp_path / "missing" / "history.sqlite3"
    output = tmp_path / "repair" / "history.sqlite3"

    with pytest.raises(FileNotFoundError):
        repair_database(missing, output)

    assert not missing.exists()
    assert not output.exists()


def test_reports_are_utf8_and_machine_readable(tmp_path: Path) -> None:
    source = make_history(
        tmp_path / "Genre_test_Музыка" / ".genre_test" / "history.sqlite3",
        tracks=2,
    )
    reports = scan_databases([source.parent.parent], full_integrity=True)
    targets = write_scan_reports(reports, tmp_path / "reports" / "scan")

    payload = json.loads(targets["json"].read_text(encoding="utf-8"))
    markdown = targets["markdown"].read_text(encoding="utf-8")

    assert payload["candidate_count"] == 1
    assert "Музыка" in payload["candidates"][0]["path"]
    assert "Музыка" in markdown

    repaired = tmp_path / "repair" / "history.sqlite3"
    repair = repair_database(source, repaired)
    repair_targets = write_repair_report(
        repair,
        tmp_path / "reports" / "repair",
    )
    repair_json = json.loads(repair_targets["json"].read_text(encoding="utf-8"))

    assert repair_json["source_unchanged"] is True
    assert repair_json["output_kind"] == "history"


def test_cli_audit_returns_nonzero_for_invalid_database(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    broken = tmp_path / "Genre_test_broken" / "history.sqlite3"
    broken.parent.mkdir(parents=True)
    broken.write_bytes(b"bad sqlite")

    code = main(["audit", str(broken), "--full-integrity"])
    captured = capsys.readouterr()

    assert code == 2
    payload = json.loads(captured.out)
    assert payload["healthy"] is False
    assert "not a database" in payload["error"]
