from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest

from genre_test.process_owner import ProcessOwner, ProcessOwnerError, python_command


def _pid_is_running(pid: int) -> bool:
    if os.name == "posix":
        stat = Path(f"/proc/{pid}/stat")
        if stat.is_file():
            try:
                fields = stat.read_text(encoding="utf-8").split()
            except OSError:
                return False
            if len(fields) > 2 and fields[2] == "Z":
                return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _wait_not_running(pid: int, timeout: float = 3.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _pid_is_running(pid):
            return
        time.sleep(0.05)
    assert not _pid_is_running(pid), f"pid {pid} survived owned-tree shutdown"


def test_owner_rejects_invalid_lifecycle_and_command() -> None:
    owner = ProcessOwner()
    with pytest.raises(ProcessOwnerError, match="has not started"):
        owner.wait()
    with pytest.raises(ValueError, match="command"):
        owner.spawn([])
    with pytest.raises(ValueError, match="argv"):
        owner.spawn([""])

    owner.close()
    owner.close()
    assert owner.closed is True
    with pytest.raises(ProcessOwnerError, match="closed"):
        owner.spawn(python_command("pass"))


def test_owner_tracks_normal_process_exit() -> None:
    owner = ProcessOwner()
    process = owner.spawn(python_command("raise SystemExit(7)"))
    result = owner.wait(timeout=5)
    assert result.pid == process.pid
    assert result.returncode == 7
    owner.close()
    assert owner.closed is True


def test_owner_accepts_explicit_cwd_and_environment(tmp_path: Path) -> None:
    env = dict(os.environ)
    env["GENRE_TEST_OWNER_FIXTURE"] = "owned"
    code = (
        "import os, pathlib; "
        "assert pathlib.Path.cwd() == pathlib.Path(os.environ['EXPECTED_CWD']); "
        "assert os.environ['GENRE_TEST_OWNER_FIXTURE'] == 'owned'"
    )
    env["EXPECTED_CWD"] = str(tmp_path)
    with ProcessOwner() as owner:
        owner.spawn(python_command(code), cwd=tmp_path, env=env)
        assert owner.wait(timeout=5).returncode == 0


def test_owner_allows_only_one_root_operation() -> None:
    with ProcessOwner() as owner:
        owner.spawn(python_command("import time; time.sleep(10)"))
        with pytest.raises(ProcessOwnerError, match="already owns"):
            owner.spawn(python_command("pass"))


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group contract")
def test_posix_close_kills_child_process_tree() -> None:
    parent_code = r'''
import subprocess
import sys
import time
child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
print(child.pid, flush=True)
time.sleep(30)
'''
    owner = ProcessOwner(terminate_timeout=0.3)
    process = owner.spawn(
        python_command(parent_code),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stdout is not None
    child_pid = int(process.stdout.readline().strip())
    assert _pid_is_running(process.pid)
    assert _pid_is_running(child_pid)

    owner.close()

    assert process.poll() is not None
    _wait_not_running(child_pid)


@pytest.mark.skipif(os.name != "posix", reason="POSIX escalation contract")
def test_posix_close_escalates_when_sigterm_is_ignored() -> None:
    code = r'''
import signal
import time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
print("ready", flush=True)
time.sleep(30)
'''
    owner = ProcessOwner(terminate_timeout=0.05)
    process = owner.spawn(python_command(code), stdout=subprocess.PIPE, text=True)
    assert process.stdout is not None
    assert process.stdout.readline().strip() == "ready"
    owner.close()
    assert process.poll() is not None


def test_context_manager_closes_operation_on_exception() -> None:
    process = None
    with (
        pytest.raises(RuntimeError, match="fixture"),
        ProcessOwner(terminate_timeout=0.1) as owner,
    ):
        process = owner.spawn(python_command("import time; time.sleep(30)"))
        raise RuntimeError("fixture")
    assert process is not None
    assert process.poll() is not None


def test_windows_contract_source_contains_kill_on_close_and_gate() -> None:
    source = Path(__file__).parents[1] / "src" / "genre_test" / "process_owner.py"
    text = source.read_text(encoding="utf-8")
    assert "0x00002000" in text
    assert "AssignProcessToJobObject" in text
    assert "TerminateJobObject" in text
    assert "_WINDOWS_BOOTSTRAP" in text
    assert "WaitForSingleObject" in text
    assert "SetEvent" in text
