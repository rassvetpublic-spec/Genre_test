from __future__ import annotations

import os
import signal
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any


class ProcessOwnerError(RuntimeError):
    """Raised when an external operation cannot be safely owned."""


@dataclass(frozen=True)
class ProcessExit:
    pid: int
    returncode: int


class _WindowsJob:
    """Minimal Win32 Job Object wrapper with kill-on-close semantics."""

    def __init__(self) -> None:
        if os.name != "nt":
            raise ProcessOwnerError("Windows Job Object requested on a non-Windows host")
        import ctypes
        from ctypes import wintypes

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_ulonglong),
                ("WriteOperationCount", ctypes.c_ulonglong),
                ("OtherOperationCount", ctypes.c_ulonglong),
                ("ReadTransferCount", ctypes.c_ulonglong),
                ("WriteTransferCount", ctypes.c_ulonglong),
                ("OtherTransferCount", ctypes.c_ulonglong),
            ]

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel32.TerminateJobObject.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        handle = kernel32.CreateJobObjectW(None, None)
        if not handle:
            raise ProcessOwnerError(
                f"CreateJobObjectW failed with Win32 error {ctypes.get_last_error()}"
            )

        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = 0x00002000  # KILL_ON_JOB_CLOSE
        ok = kernel32.SetInformationJobObject(
            handle,
            9,  # JobObjectExtendedLimitInformation
            ctypes.byref(info),
            ctypes.sizeof(info),
        )
        if not ok:
            error = ctypes.get_last_error()
            kernel32.CloseHandle(handle)
            raise ProcessOwnerError(
                f"SetInformationJobObject failed with Win32 error {error}"
            )

        self._ctypes = ctypes
        self._kernel32 = kernel32
        self._handle = handle

    @property
    def closed(self) -> bool:
        return self._handle is None

    def assign(self, process: subprocess.Popen[Any]) -> None:
        if self._handle is None:
            raise ProcessOwnerError("cannot assign a process to a closed Job Object")
        process_handle = getattr(process, "_handle", None)
        if process_handle is None:
            raise ProcessOwnerError("subprocess does not expose a Windows process handle")
        if not self._kernel32.AssignProcessToJobObject(self._handle, process_handle):
            error = self._ctypes.get_last_error()
            raise ProcessOwnerError(
                f"AssignProcessToJobObject failed with Win32 error {error}"
            )

    def terminate(self, exit_code: int = 1) -> None:
        if self._handle is None:
            return
        if not self._kernel32.TerminateJobObject(self._handle, exit_code):
            error = self._ctypes.get_last_error()
            raise ProcessOwnerError(
                f"TerminateJobObject failed with Win32 error {error}"
            )

    def close(self) -> None:
        if self._handle is None:
            return
        handle = self._handle
        self._handle = None
        if not self._kernel32.CloseHandle(handle):
            error = self._ctypes.get_last_error()
            raise ProcessOwnerError(f"CloseHandle failed with Win32 error {error}")


class ProcessOwner:
    """Own one external operation and its complete process subtree.

    POSIX launches a new session and terminates/kills the corresponding process
    group. Windows assigns the root process to a Job Object configured with
    ``JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE``. Closing the owner is idempotent.
    """

    def __init__(self, *, terminate_timeout: float = 3.0) -> None:
        if terminate_timeout < 0:
            raise ValueError("terminate_timeout must be >= 0")
        self.terminate_timeout = float(terminate_timeout)
        self._process: subprocess.Popen[Any] | None = None
        self._windows_job: _WindowsJob | None = None
        self._closed = False

    @property
    def process(self) -> subprocess.Popen[Any] | None:
        return self._process

    @property
    def closed(self) -> bool:
        return self._closed

    def spawn(
        self,
        command: Sequence[str | os.PathLike[str]],
        *,
        cwd: str | os.PathLike[str] | None = None,
        env: Mapping[str, str] | None = None,
        stdin: int | IO[Any] | None = None,
        stdout: int | IO[Any] | None = None,
        stderr: int | IO[Any] | None = None,
        text: bool = False,
    ) -> subprocess.Popen[Any]:
        if self._closed:
            raise ProcessOwnerError("cannot spawn from a closed ProcessOwner")
        if self._process is not None:
            raise ProcessOwnerError("ProcessOwner already owns an operation")
        argv = [os.fspath(part) for part in command]
        if not argv or any(not part for part in argv):
            raise ValueError("command must contain non-empty argv entries")

        kwargs: dict[str, Any] = {
            "cwd": None if cwd is None else os.fspath(Path(cwd)),
            "env": None if env is None else dict(env),
            "stdin": stdin,
            "stdout": stdout,
            "stderr": stderr,
            "text": text,
            "shell": False,
        }
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True

        try:
            process = subprocess.Popen(argv, **kwargs)
        except OSError as exc:
            raise ProcessOwnerError(f"failed to start owned process: {type(exc).__name__}") from exc

        try:
            if os.name == "nt":
                job = _WindowsJob()
                try:
                    job.assign(process)
                except BaseException:
                    job.close()
                    raise
                self._windows_job = job
            self._process = process
            return process
        except BaseException:
            self._terminate_unowned_root(process)
            raise

    def wait(self, timeout: float | None = None) -> ProcessExit:
        process = self._require_process()
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            raise
        return ProcessExit(pid=process.pid, returncode=returncode)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        process = self._process
        if process is None:
            return
        if process.poll() is None:
            if os.name == "nt":
                self._terminate_windows_tree(process)
            else:
                self._terminate_posix_tree(process)
        self._close_windows_job()

    def _terminate_posix_tree(self, process: subprocess.Popen[Any]) -> None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=self.terminate_timeout)
            return
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=max(1.0, self.terminate_timeout))
        except subprocess.TimeoutExpired as exc:
            raise ProcessOwnerError("owned POSIX process group did not terminate") from exc

    def _terminate_windows_tree(self, process: subprocess.Popen[Any]) -> None:
        job = self._windows_job
        if job is None:
            self._terminate_unowned_root(process)
            return
        job.terminate(1)
        try:
            process.wait(timeout=max(1.0, self.terminate_timeout))
        except subprocess.TimeoutExpired as exc:
            raise ProcessOwnerError("owned Windows Job Object did not terminate") from exc

    def _close_windows_job(self) -> None:
        job = self._windows_job
        self._windows_job = None
        if job is not None:
            job.close()

    @staticmethod
    def _terminate_unowned_root(process: subprocess.Popen[Any]) -> None:
        if process.poll() is not None:
            return
        try:
            process.kill()
        except OSError:
            return
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass

    def _require_process(self) -> subprocess.Popen[Any]:
        if self._process is None:
            raise ProcessOwnerError("ProcessOwner has not started an operation")
        return self._process

    def __enter__(self) -> ProcessOwner:
        if self._closed:
            raise ProcessOwnerError("cannot enter a closed ProcessOwner")
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()


def python_command(code: str) -> list[str]:
    """Return an argv-safe command for a Python fixture/helper process."""

    return [sys.executable, "-c", code]
