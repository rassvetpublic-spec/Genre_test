from __future__ import annotations

import queue
import subprocess
import threading
import uuid
from collections import deque
from pathlib import Path
from typing import Any, Self

from .contracts import (
    EmbeddingIdentity,
    EmbeddingVector,
    RetrievalBackendInfo,
    RetrievalHealth,
)
from .model_pins import (
    CLAMP3_CODE_REVISION,
    CLAMP3_WEIGHT_FILENAME,
    CLAMP3_WEIGHT_SHA256,
    EMBEDDING_DIMENSION,
    MERT_MODEL_ID,
    MERT_REVISION,
    PREPROCESSING_VERSION,
    TEXT_MODEL_ID,
    TEXT_MODEL_REVISION,
)
from .sidecar_protocol import (
    SidecarProtocolError,
    SidecarRequest,
    SidecarResponse,
    decode_vector_f32,
)


class Clamp3SidecarError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def default_clamp3_backend_info() -> RetrievalBackendInfo:
    return RetrievalBackendInfo(
        backend_name="clamp3-saas-sidecar",
        backend_version="1",
        clamp_code_revision=CLAMP3_CODE_REVISION,
        clamp_weight_name=CLAMP3_WEIGHT_FILENAME,
        clamp_weight_sha256=CLAMP3_WEIGHT_SHA256,
        mert_model_id=MERT_MODEL_ID,
        mert_revision=MERT_REVISION,
        text_model_id=TEXT_MODEL_ID,
        text_model_revision=TEXT_MODEL_REVISION,
        text_tokenizer_revision=TEXT_MODEL_REVISION,
        preprocessing_version=PREPROCESSING_VERSION,
        embedding_dim=EMBEDDING_DIMENSION,
    )


class Clamp3SidecarBackend:
    """Persistent JSON-lines client for the isolated CLaMP 3 runtime.

    The heavy model stack lives in a separate Python process. The core process only
    owns the small transport/client layer and the immutable backend identity.
    """

    def __init__(
        self,
        *,
        python_executable: Path,
        script_path: Path,
        runtime_root: Path,
        upstream_root: Path | None = None,
        request_timeout_s: float = 120.0,
        info: RetrievalBackendInfo | None = None,
    ) -> None:
        if request_timeout_s <= 0:
            raise ValueError("request_timeout_s must be positive")
        self.python_executable = Path(python_executable)
        self.script_path = Path(script_path)
        self.runtime_root = Path(runtime_root)
        self.upstream_root = (
            Path(upstream_root)
            if upstream_root is not None
            else self.runtime_root / "upstream" / "clamp3"
        )
        self.request_timeout_s = float(request_timeout_s)
        self._info = info or default_clamp3_backend_info()
        self._process: subprocess.Popen[str] | None = None
        self._responses: queue.Queue[str | Exception] = queue.Queue()
        self._request_lock = threading.Lock()
        self._stderr_tail: deque[str] = deque(maxlen=50)
        self._stdout_thread: threading.Thread | None = None
        self._stderr_thread: threading.Thread | None = None

    @classmethod
    def from_repo_defaults(
        cls,
        repo_root: Path,
        *,
        request_timeout_s: float = 120.0,
    ) -> Clamp3SidecarBackend:
        repo_root = Path(repo_root)
        runtime_root = repo_root / ".genre_test" / "retrieval"
        return cls(
            python_executable=runtime_root / "runtime" / ".venv" / "Scripts" / "python.exe",
            script_path=repo_root / "scripts" / "clamp3_sidecar.py",
            runtime_root=runtime_root,
            request_timeout_s=request_timeout_s,
        )

    @property
    def info(self) -> RetrievalBackendInfo:
        return self._info

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    @property
    def stderr_tail(self) -> tuple[str, ...]:
        return tuple(self._stderr_tail)

    def _start(self) -> None:
        if self.is_running:
            return
        if not self.python_executable.is_file():
            raise Clamp3SidecarError(
                "RUNTIME_MISSING",
                f"isolated Python interpreter not found: {self.python_executable}",
            )
        if not self.script_path.is_file():
            raise Clamp3SidecarError(
                "SIDECAR_SCRIPT_MISSING",
                f"sidecar script not found: {self.script_path}",
            )

        command = [
            str(self.python_executable),
            "-u",
            str(self.script_path),
            "--runtime-root",
            str(self.runtime_root),
            "--upstream-root",
            str(self.upstream_root),
        ]
        self._process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        assert self._process.stdout is not None
        assert self._process.stderr is not None
        self._stdout_thread = threading.Thread(
            target=self._read_stdout,
            name="genre-test-clamp3-sidecar-stdout",
            daemon=True,
        )
        self._stderr_thread = threading.Thread(
            target=self._read_stderr,
            name="genre-test-clamp3-sidecar-stderr",
            daemon=True,
        )
        self._stdout_thread.start()
        self._stderr_thread.start()

    def _read_stdout(self) -> None:
        process = self._process
        if process is None or process.stdout is None:
            return
        try:
            for line in process.stdout:
                stripped = line.strip()
                if stripped:
                    self._responses.put(stripped)
        except (OSError, ValueError) as exc:  # pragma: no cover - defensive thread boundary
            self._responses.put(exc)

    def _read_stderr(self) -> None:
        process = self._process
        if process is None or process.stderr is None:
            return
        try:
            for line in process.stderr:
                stripped = line.rstrip()
                if stripped:
                    self._stderr_tail.append(stripped)
        except (OSError, ValueError):  # pragma: no cover - diagnostics must not crash client
            return

    def _request(self, op: str, payload: dict[str, Any]) -> SidecarResponse:
        with self._request_lock:
            self._start()
            process = self._process
            if process is None or process.stdin is None:
                raise Clamp3SidecarError("SIDECAR_START_FAILED", "sidecar process has no stdin")
            request = SidecarRequest(op=op, request_id=uuid.uuid4().hex, payload=payload)
            try:
                process.stdin.write(request.to_json() + "\n")
                process.stdin.flush()
            except (BrokenPipeError, OSError) as exc:
                self._raise_process_failure("SIDECAR_PIPE_FAILED", exc)

            try:
                raw = self._responses.get(timeout=self.request_timeout_s)
            except queue.Empty as exc:
                self._raise_process_failure("SIDECAR_TIMEOUT", exc)

            if isinstance(raw, Exception):
                raise Clamp3SidecarError("SIDECAR_READER_FAILED", str(raw))
            response = SidecarResponse.from_json(raw)
            if response.request_id != request.request_id:
                raise SidecarProtocolError(
                    "sidecar response request_id does not match the active request"
                )
            if not response.ok:
                raise Clamp3SidecarError(
                    response.error_code or "SIDECAR_ERROR",
                    response.error_message or "sidecar operation failed",
                )
            return response

    def _raise_process_failure(self, code: str, cause: Exception) -> None:
        process = self._process
        return_code = process.poll() if process is not None else None
        stderr = "\n".join(self._stderr_tail[-10:])
        detail = f"{cause}; return_code={return_code}"
        if stderr:
            detail += f"; stderr_tail={stderr}"
        raise Clamp3SidecarError(code, detail) from cause

    def health(self) -> RetrievalHealth:
        if not self.python_executable.is_file():
            return RetrievalHealth(
                "N/A",
                "Retrieval runtime not installed",
                f"Missing isolated Python: {self.python_executable}",
                backend_name=self.info.backend_name,
            )
        if not self.script_path.is_file():
            return RetrievalHealth(
                "FAIL",
                "Retrieval sidecar missing",
                f"Missing sidecar script: {self.script_path}",
                backend_name=self.info.backend_name,
            )
        try:
            response = self._request("health", {})
        except (Clamp3SidecarError, SidecarProtocolError) as exc:
            return RetrievalHealth(
                "FAIL",
                "Retrieval sidecar unavailable",
                str(exc),
                backend_name=self.info.backend_name,
            )
        status = str(response.payload.get("status", "WARN"))
        if status not in {"OK", "WARN", "FAIL", "N/A"}:
            status = "WARN"
        value = str(response.payload.get("value", "CLaMP 3 sidecar"))
        details = str(response.payload.get("details", ""))
        return RetrievalHealth(
            status,  # type: ignore[arg-type]
            value,
            details,
            backend_name=self.info.backend_name,
        )

    def embed_text(self, text: str, *, language: str | None = None) -> EmbeddingVector:
        identity = EmbeddingIdentity.for_text(
            self.info.fingerprint,
            text,
            language=language,
        )
        response = self._request(
            "embed_text",
            {"text": text.strip(), "language": identity.language},
        )
        values = decode_vector_f32(response.payload.get("vector", {}))
        return EmbeddingVector.normalized(
            identity,
            values,
            expected_dim=self.info.embedding_dim,
        )

    def embed_audio(
        self,
        path: Path,
        *,
        track_id: str,
        start_s: float | None = None,
        end_s: float | None = None,
    ) -> EmbeddingVector:
        audio_path = Path(path)
        if not audio_path.is_file():
            raise FileNotFoundError(audio_path)
        if not track_id.strip():
            raise ValueError("track_id must not be empty")
        if (start_s is None) != (end_s is None):
            raise ValueError("start_s and end_s must be supplied together")

        if start_s is None:
            identity = EmbeddingIdentity(
                backend_fingerprint=self.info.fingerprint,
                scope="full",
                track_id=track_id,
            )
        else:
            assert end_s is not None
            identity = EmbeddingIdentity(
                backend_fingerprint=self.info.fingerprint,
                scope="segment",
                track_id=track_id,
                start_s=float(start_s),
                end_s=float(end_s),
            )

        response = self._request(
            "embed_audio",
            {
                "path": str(audio_path.resolve()),
                "track_id": track_id,
                "start_s": start_s,
                "end_s": end_s,
            },
        )
        values = decode_vector_f32(response.payload.get("vector", {}))
        return EmbeddingVector.normalized(
            identity,
            values,
            expected_dim=self.info.embedding_dim,
        )

    def close(self) -> None:
        process = self._process
        if process is None:
            return
        if process.poll() is None:
            try:
                self._request("shutdown", {})
            except (Clamp3SidecarError, SidecarProtocolError):
                pass
        try:
            process.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5.0)
        self._process = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()
