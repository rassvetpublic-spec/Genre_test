import sqlite3

from genre_test.logging_utils import append_log
from genre_test.runtime_meta import (
    default_hf_home,
    default_history_path,
    default_log_path,
    default_results_dir,
    default_state_dir,
)


def test_default_runtime_paths_stay_inside_project_root(tmp_path, monkeypatch):
    monkeypatch.setenv("GENRE_TEST_PROJECT_ROOT", str(tmp_path))
    monkeypatch.delenv("GENRE_TEST_DATA_DIR", raising=False)

    assert default_state_dir() == tmp_path / ".genre_test"
    assert default_history_path() == tmp_path / ".genre_test" / "history.sqlite3"
    assert default_log_path() == tmp_path / ".genre_test" / "logs" / "genre_test.log"
    assert default_hf_home() == tmp_path / ".genre_test" / "huggingface"
    assert default_results_dir() == tmp_path / "results"


def test_legacy_history_is_copied_to_repo_local_database(tmp_path, monkeypatch):
    project = tmp_path / "project"
    legacy_root = tmp_path / "legacy"
    legacy_db = legacy_root / "Genre_test" / "history.sqlite3"
    legacy_db.parent.mkdir(parents=True)
    with sqlite3.connect(legacy_db) as conn:
        conn.execute("CREATE TABLE marker(value TEXT)")
        conn.execute("INSERT INTO marker(value) VALUES ('preserved')")

    monkeypatch.setenv("GENRE_TEST_PROJECT_ROOT", str(project))
    monkeypatch.setenv("XDG_DATA_HOME", str(legacy_root))
    monkeypatch.delenv("GENRE_TEST_DATA_DIR", raising=False)

    target = default_history_path()
    assert target == project / ".genre_test" / "history.sqlite3"
    with sqlite3.connect(target) as conn:
        value = conn.execute("SELECT value FROM marker").fetchone()[0]
    assert value == "preserved"


def test_log_is_written_inside_project_root(tmp_path, monkeypatch):
    monkeypatch.setenv("GENRE_TEST_PROJECT_ROOT", str(tmp_path))
    monkeypatch.delenv("GENRE_TEST_DATA_DIR", raising=False)

    target = append_log("test message")
    assert target == tmp_path / ".genre_test" / "logs" / "genre_test.log"
    assert "test message" in target.read_text(encoding="utf-8")
