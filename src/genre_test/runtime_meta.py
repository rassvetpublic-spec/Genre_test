from __future__ import annotations

import os
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

RESULT_SCHEMA_VERSION = 2


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def new_run_id() -> str:
    return str(uuid.uuid4())


def project_root() -> Path:
    """Return the checkout root for the editable/source installation."""
    explicit = os.environ.get("GENRE_TEST_PROJECT_ROOT")
    if explicit:
        return Path(explicit).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def default_state_dir() -> Path:
    explicit = os.environ.get("GENRE_TEST_DATA_DIR")
    if explicit:
        return Path(explicit).expanduser().resolve()
    return project_root() / ".genre_test"


def default_history_path() -> Path:
    return default_state_dir() / "history.sqlite3"


def default_log_path() -> Path:
    return default_state_dir() / "logs" / "genre_test.log"


def default_hf_home() -> Path:
    return default_state_dir() / "huggingface"


def default_results_dir() -> Path:
    return project_root() / "results"


def legacy_history_path() -> Path | None:
    """Return the pre-v0.3.1 history location, if the platform had one."""
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "Genre_test" / "history.sqlite3"
    if os.environ.get("XDG_DATA_HOME"):
        return Path(os.environ["XDG_DATA_HOME"]) / "Genre_test" / "history.sqlite3"
    if os.name != "nt":
        return Path.home() / ".local" / "share" / "Genre_test" / "history.sqlite3"
    return None


def current_git_commit() -> str | None:
    explicit = os.environ.get("GENRE_TEST_GIT_COMMIT")
    if explicit:
        return explicit.strip() or None

    repo_root = project_root()
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = proc.stdout.strip()
    return value or None
