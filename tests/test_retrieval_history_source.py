from __future__ import annotations

import io
import json
import sqlite3
import sys
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

import pytest

from genre_test.retrieval import entrypoint
from genre_test.retrieval.history_source import (
    HISTORY_SOURCE_ERROR_CODES,
    HistorySourceError,
    resolve_history_source,
    validate_explicit_history,
)


def _valid_history(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE tracks (track_id TEXT PRIMARY KEY, last_path TEXT)"
        )
        connection.execute(
            "CREATE TABLE runs (track_id TEXT, result_json TEXT, analyzed_at TEXT)"
        )


def test_missing_explicit_history_fails_without_creating_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.sqlite3"

    with pytest.raises(HistorySourceError) as captured:
        validate_explicit_history(missing)

    assert captured.value.failure.code == "history_source_missing"
    assert captured.value.to_dict()["error"] == "history_source_error"
    assert not missing.exists()


def test_invalid_explicit_history_schema_fails_read_only(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.sqlite3"
    with sqlite3.connect(invalid) as connection:
        connection.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")

    before_size = invalid.stat().st_size
    with pytest.raises(HistorySourceError) as captured:
        validate_explicit_history(invalid)

    assert captured.value.failure.code == "history_source_invalid_schema"
    assert captured.value.failure.missing_tables == ("runs", "tracks")
    assert invalid.stat().st_size == before_size
    with sqlite3.connect(invalid) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    assert tables == {"unrelated"}


def test_required_history_columns_are_validated(tmp_path: Path) -> None:
    invalid = tmp_path / "columns.sqlite3"
    with sqlite3.connect(invalid) as connection:
        connection.execute("CREATE TABLE tracks (track_id TEXT PRIMARY KEY)")
        connection.execute("CREATE TABLE runs (track_id TEXT, result_json TEXT)")

    with pytest.raises(HistorySourceError) as captured:
        validate_explicit_history(invalid)

    assert captured.value.failure.code == "history_source_invalid_schema"
    assert captured.value.failure.missing_columns == (
        "tracks.last_path",
        "runs.analyzed_at",
    )


def test_runs_without_rowid_is_rejected_before_dispatch(tmp_path: Path) -> None:
    invalid = tmp_path / "without-rowid.sqlite3"
    with sqlite3.connect(invalid) as connection:
        connection.execute(
            "CREATE TABLE tracks (track_id TEXT PRIMARY KEY, last_path TEXT)"
        )
        connection.execute(
            """
            CREATE TABLE runs (
                run_id TEXT PRIMARY KEY,
                track_id TEXT,
                result_json TEXT,
                analyzed_at TEXT
            ) WITHOUT ROWID
            """
        )

    with pytest.raises(HistorySourceError) as captured:
        validate_explicit_history(invalid)

    assert captured.value.failure.code == "history_source_invalid_schema"
    assert "runs.rowid" in captured.value.failure.message


def test_valid_explicit_history_passes(tmp_path: Path) -> None:
    history = tmp_path / "history.sqlite3"
    _valid_history(history)

    assert validate_explicit_history(history) == history


def test_implicit_default_history_is_not_prevalidated(tmp_path: Path) -> None:
    default = tmp_path / "not-created-yet.sqlite3"

    resolved = resolve_history_source(explicit_path=None, default_path=default)

    assert resolved == default
    assert not default.exists()


@pytest.mark.parametrize(
    "command",
    [
        "retrieval-index-status",
        "index",
        "segment-status",
        "segment-index",
        "search-text",
        "search-audio",
        "catalog-audit",
        "retry-missing",
        "benchmark-run",
    ],
)
def test_all_history_consuming_command_families_share_pre_dispatch_validation(
    tmp_path: Path,
    command: str,
) -> None:
    missing = tmp_path / f"{command}.sqlite3"

    with pytest.raises(HistorySourceError) as captured:
        entrypoint.validate_explicit_history_argv(
            [command, "placeholder", "--history", str(missing)]
        )

    assert captured.value.failure.code == "history_source_missing"
    assert not missing.exists()


def test_history_equals_syntax_uses_same_contract(tmp_path: Path) -> None:
    missing = tmp_path / "missing.sqlite3"

    with pytest.raises(HistorySourceError):
        entrypoint.validate_explicit_history_argv(
            ["catalog-audit", f"--history={missing}"]
        )

    assert not missing.exists()


def test_empty_history_equals_is_stable_invalid_path_error() -> None:
    with pytest.raises(HistorySourceError) as captured:
        entrypoint.validate_explicit_history_argv(["status", "--history="])

    assert captured.value.failure.code == "history_source_invalid_path"
    assert captured.value.failure.path == ""


def test_single_dash_history_value_is_not_skipped() -> None:
    paths = entrypoint.explicit_history_paths(
        ["status", "--history", "-missing.sqlite3"]
    )

    assert paths == (Path("-missing.sqlite3"),)


def test_option_scanning_stops_at_double_dash() -> None:
    paths = entrypoint.explicit_history_paths(
        ["search-text", "--", "--history=/missing.sqlite3"]
    )

    assert paths == ()


def test_non_history_command_leaves_history_token_to_typer() -> None:
    paths = entrypoint.explicit_history_paths(
        ["exit-codes", "--history", "missing.sqlite3"]
    )

    assert paths == ()


def test_machine_error_vocabulary_matches_canonical_contract() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    contract = (repo_root / "docs/RETRIEVAL_HISTORY_SOURCE_CONTRACT.md").read_text(
        encoding="utf-8"
    )

    assert HISTORY_SOURCE_ERROR_CODES == {
        "history_source_missing",
        "history_source_invalid_path",
        "history_source_invalid_schema",
        "history_source_corrupt",
        "history_source_unreadable",
    }
    for code in HISTORY_SOURCE_ERROR_CODES:
        assert f"`{code}`" in contract


def test_entrypoint_maps_missing_explicit_history_to_stable_source_exit(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.sqlite3"
    stderr = io.StringIO()

    with (
        patch.object(
            sys,
            "argv",
            ["genre-test-retrieval", "retrieval-index-status", "--history", str(missing)],
        ),
        patch("genre_test.retrieval.cli.main") as cli_main,
        redirect_stderr(stderr),
        pytest.raises(SystemExit) as captured,
    ):
        entrypoint.main()

    assert captured.value.code == 23
    cli_main.assert_not_called()
    payload = json.loads(stderr.getvalue())
    assert payload["error"] == "history_source_error"
    assert payload["code"] == "history_source_missing"
    assert payload["path"] == str(missing)
    assert not missing.exists()


def test_entrypoint_maps_invalid_schema_to_same_source_exit(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.sqlite3"
    with sqlite3.connect(invalid) as connection:
        connection.execute("CREATE TABLE tracks (track_id TEXT, last_path TEXT)")
    stderr = io.StringIO()

    with (
        patch.object(
            sys,
            "argv",
            ["genre-test-retrieval", "catalog-audit", "--history", str(invalid)],
        ),
        patch("genre_test.retrieval.cli.main") as cli_main,
        redirect_stderr(stderr),
        pytest.raises(SystemExit) as captured,
    ):
        entrypoint.main()

    assert captured.value.code == 23
    cli_main.assert_not_called()
    payload = json.loads(stderr.getvalue())
    assert payload["code"] == "history_source_invalid_schema"
    assert payload["missing_tables"] == ["runs"]
