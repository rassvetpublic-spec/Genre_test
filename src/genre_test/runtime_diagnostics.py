from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeDiagnostics:
    ffmpeg_path: str | None
    hf_token_available: bool
    hf_auth_source: str

    @property
    def ffmpeg_available(self) -> bool:
        return self.ffmpeg_path is not None

    @property
    def decoder_warning(self) -> str | None:
        if self.ffmpeg_available:
            return None
        return "FFmpeg НЕ НАЙДЕН — AAC/M4A и расширенный decode fallback недоступны"

    @property
    def hf_auth_label(self) -> str:
        if self.hf_token_available:
            return f"token available ({self.hf_auth_source}; not network-validated)"
        return "anonymous (no token found)"


def _hf_token_status() -> tuple[bool, str]:
    if os.environ.get("HF_TOKEN"):
        return True, "HF_TOKEN"
    if os.environ.get("HUGGING_FACE_HUB_TOKEN"):
        return True, "HUGGING_FACE_HUB_TOKEN"
    try:
        from huggingface_hub import get_token
    except ImportError:  # pragma: no cover - transformers normally installs this dependency
        return False, "huggingface_hub unavailable"
    try:
        token = get_token()
    except OSError:  # pragma: no cover - damaged/unreadable local HF token cache
        return False, "token cache unreadable"
    return (True, "huggingface_hub cache") if token else (False, "none")


def _ffmpeg_candidates() -> list[Path]:
    candidates: list[Path] = []

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe")

    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        candidates.append(Path(user_profile) / "scoop" / "shims" / "ffmpeg.exe")

    program_data = os.environ.get("ProgramData")
    if program_data:
        candidates.append(Path(program_data) / "chocolatey" / "bin" / "ffmpeg.exe")

    program_files = os.environ.get("ProgramFiles")
    if program_files:
        candidates.append(Path(program_files) / "ffmpeg" / "bin" / "ffmpeg.exe")

    return candidates


def _prepend_to_process_path(directory: Path) -> None:
    directory_text = str(directory)
    entries = [entry for entry in os.environ.get("PATH", "").split(os.pathsep) if entry]
    if directory_text not in entries:
        os.environ["PATH"] = os.pathsep.join([directory_text, *entries])


def find_ffmpeg() -> str | None:
    path = shutil.which("ffmpeg")
    if path:
        return path

    for candidate in _ffmpeg_candidates():
        if candidate.is_file():
            resolved = candidate.resolve()
            _prepend_to_process_path(resolved.parent)
            return str(resolved)
    return None


def collect_runtime_diagnostics() -> RuntimeDiagnostics:
    token_available, token_source = _hf_token_status()
    return RuntimeDiagnostics(
        ffmpeg_path=find_ffmpeg(),
        hf_token_available=token_available,
        hf_auth_source=token_source,
    )
