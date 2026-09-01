from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from genre_test.db_access_journal import (
    access_summary,
    default_journal_path,
    read_database_provenance,
    record_database_access,
)
from genre_test.retrieval.catalog import load_catalog_tracks
from genre_test.retrieval.history_scope import _source_fingerprint, build_history_scope


@pytest.fixture(autouse=True)
def _isolated_genre_test_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GENRE_TEST_DATA_DIR", str(tmp_path / "state"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _create_source(path: Path, *, duplicate: bool = False) -> None:
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE tracks (
            track_id TEXT PRIMARY KEY,
            sha256 TEXT,
            first_seen_at TEXT,
            last_seen_at TEXT,
            last_path TEXT,
            file_size INTEGER
        );
        CREATE TABLE runs (
            run_id TEXT PRIMARY KEY,
            track_id TEXT NOT NULL,
            analyzed_at TEXT NOT NULL,
            analyzer_version TEXT,
            analysis_mode TEXT,
            source_path TEXT,
            result_json TEXT
        );
        CREATE INDEX idx_runs_track_id ON runs(track_id);
        CREATE INDEX idx_runs_scope ON runs(analyzer_version, analysis_mode);
        """
    )
    tracks = [
        ("sha256:a", "a", "2026-01-01", "2026-01-05", "D:/newer/a.wav", 10),
        ("sha256:b", "b", "2026-01-01", "2026-01-05", "D:/newer/b.wav", 20),
        ("sha256:c", "c", "2026-01-01", "2026-01-05", "D:/older/c.wav", 30),
        ("sha256:d", "d", "2026-01-01", "2026-01-05", "D:/fast/d.wav", 40),
    ]
    con.executemany("INSERT INTO tracks VALUES (?, ?, ?, ?, ?, ?)", tracks)
    runs = [
        (
            "run-a",
            "sha256:a",
            "2026-01-02T00:00:00Z",
            "0.4.0",
            "auto",
            "D:/music/a.wav",
            json.dumps({"path": "D:/music/a.wav", "resolved_genre": "Rock"}),
        ),
        (
            "run-b",
            "sha256:b",
            "2026-01-03T00:00:00Z",
            "0.4.0",
            "auto",
            "D:/music/b-v04.wav",
            json.dumps({"path": "D:/music/b-v04.wav", "resolved_genre": "Pop"}),
        ),
        (
            "run-c",
            "sha256:c",
            "2026-01-04T00:00:00Z",
            "0.3.0",
            "auto",
            "D:/older/c.wav",
            json.dumps({"path": "D:/older/c.wav", "resolved_genre": "Jazz"}),
        ),
        (
            "run-d",
            "sha256:d",
            "2026-01-05T00:00:00Z",
            "0.4.0",
            "fast",
            "D:/fast/d.wav",
            json.dumps({"path": "D:/fast/d.wav", "resolved_genre": "Metal"}),
        ),
    ]
    if duplicate:
        runs.append(
            (
                "run-a-latest",
                "sha256:a",
                "2026-01-06T00:00:00Z",
                "0.4.0",
                "auto",
                "D:/music/a-latest.wav",
                json.dumps({"path": "D:/music/a-latest.wav", "resolved_genre": "Rock"}),
            )
        )
    con.executemany("INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)", runs)
    con.commit()
    con.close()


def _create_access_journal(tmp_path: Path) -> Path:
    result = record_database_access(
        target_path=tmp_path / "journal-target.sqlite3",
        target_fingerprint="f" * 64,
        operation="read",
        access_mode="readonly",
        success=True,
    )
    assert result.recorded is True
    journal = default_journal_path()
    assert journal.is_file()
    return journal


def test_build_history_scope_filters_mixed_history_and_preserves_source(tmp_path: Path) -> None:
    source = tmp_path / "history.sqlite3"
    output = tmp_path / "v04_auto.sqlite3"
    _create_source(source)
    before = _sha256(source)

    report = build_history_scope(
        source,
        output,
        analyzer_version="0.4.0",
        analysis_mode="auto",
    )

    assert report.matching_runs == 2
    assert report.selected_tracks == 2
    assert report.duplicate_track_ids == 0
    assert report.integrity_check == "ok"
    assert report.source_unchanged is True
    assert report.journal["source"]["recorded"] is True
    assert report.journal["output"]["recorded"] is True
    assert _sha256(source) == before

    con = sqlite3.connect(output)
    assert con.execute("SELECT COUNT(*) FROM tracks").fetchone()[0] == 2
    assert con.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 2
    assert con.execute(
        "SELECT COUNT(*) FROM runs WHERE analyzer_version='0.4.0' AND analysis_mode='auto'"
    ).fetchone()[0] == 2
    assert con.execute(
        "SELECT last_path FROM tracks WHERE track_id='sha256:b'"
    ).fetchone()[0] == "D:/music/b-v04.wav"
    meta = dict(con.execute("SELECT key, value FROM retrieval_history_scope_meta"))
    provenance = read_database_provenance(con)
    con.close()
    assert meta["analyzer_version"] == "0.4.0"
    assert meta["analysis_mode"] == "auto"
    assert meta["selected_tracks"] == "2"
    assert meta["source_fingerprint_policy"] == "db+nonempty-wal-v1"
    assert provenance["status"] == "known"
    assert provenance["source_fingerprint"] == report.source_fingerprint

    source_access = access_summary(target_fingerprint=report.source_fingerprint)
    output_access = access_summary(target_fingerprint=_source_fingerprint(output))
    assert source_access.last_scope_build is not None
    assert source_access.last_read is not None
    assert output_access.last_scope_build is not None
    assert output_access.last_write is not None

    catalog = load_catalog_tracks(output)
    assert [track.track_id for track in catalog] == ["sha256:a", "sha256:b"]
    assert [track.path for track in catalog] == ["D:/music/a.wav", "D:/music/b-v04.wav"]


def test_build_history_scope_rejects_duplicate_track_ids_by_default(tmp_path: Path) -> None:
    source = tmp_path / "history.sqlite3"
    output = tmp_path / "scope.sqlite3"
    _create_source(source, duplicate=True)

    with pytest.raises(ValueError, match="duplicate track_id"):
        build_history_scope(
            source,
            output,
            analyzer_version="0.4.0",
            analysis_mode="auto",
        )

    assert not output.exists()


def test_build_history_scope_latest_policy_is_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "history.sqlite3"
    output = tmp_path / "scope.sqlite3"
    _create_source(source, duplicate=True)

    report = build_history_scope(
        source,
        output,
        analyzer_version="0.4.0",
        analysis_mode="auto",
        duplicate_policy="latest",
    )

    assert report.matching_runs == 3
    assert report.duplicate_track_ids == 1
    assert report.selected_tracks == 2

    con = sqlite3.connect(output)
    row = con.execute(
        "SELECT run_id, source_path FROM runs WHERE track_id='sha256:a'"
    ).fetchone()
    con.close()
    assert row == ("run-a-latest", "D:/music/a-latest.wav")


def test_build_history_scope_refuses_to_replace_output_without_force(tmp_path: Path) -> None:
    source = tmp_path / "history.sqlite3"
    output = tmp_path / "scope.sqlite3"
    _create_source(source)
    output.write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError):
        build_history_scope(
            source,
            output,
            analyzer_version="0.4.0",
            analysis_mode="auto",
        )

    assert output.read_text(encoding="utf-8") == "keep"


def test_scope_build_rejects_access_journal_as_source(tmp_path: Path) -> None:
    journal = _create_access_journal(tmp_path)
    before = journal.read_bytes()
    output = tmp_path / "scope.sqlite3"

    with pytest.raises(ValueError, match="access journal"):
        build_history_scope(
            journal,
            output,
            analyzer_version="0.4.0",
            analysis_mode="auto",
        )

    assert journal.read_bytes() == before
    assert not output.exists()


def test_scope_build_rejects_access_journal_as_force_output(tmp_path: Path) -> None:
    source = tmp_path / "history.sqlite3"
    _create_source(source)
    journal = _create_access_journal(tmp_path)
    before = journal.read_bytes()

    with pytest.raises(ValueError, match="access journal"):
        build_history_scope(
            source,
            journal,
            analyzer_version="0.4.0",
            analysis_mode="auto",
            force=True,
        )

    assert journal.read_bytes() == before


def test_source_fingerprint_ignores_zero_length_wal_creation(tmp_path: Path) -> None:
    source = tmp_path / "history.sqlite3"
    source.write_bytes(b"stable-db-content")

    before = _source_fingerprint(source)
    Path(str(source) + "-wal").write_bytes(b"")
    after = _source_fingerprint(source)

    assert after == before


def test_source_fingerprint_includes_nonempty_wal(tmp_path: Path) -> None:
    source = tmp_path / "history.sqlite3"
    source.write_bytes(b"stable-db-content")
    wal = Path(str(source) + "-wal")

    before = _source_fingerprint(source)
    wal.write_bytes(b"committed-wal-pages")
    after = _source_fingerprint(source)

    assert after != before
