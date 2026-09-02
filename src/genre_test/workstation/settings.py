from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ..runtime_meta import default_state_dir
from .i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES, normalize_language


@dataclass(frozen=True)
class WorkstationSettings:
    language: str = DEFAULT_LANGUAGE

    def to_dict(self) -> dict[str, str]:
        return {"language": self.language}


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path or (default_state_dir() / "workstation" / "settings.json"))

    def load(self) -> WorkstationSettings:
        if not self.path.is_file():
            return WorkstationSettings()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return WorkstationSettings()
        if not isinstance(payload, dict):
            return WorkstationSettings()
        return WorkstationSettings(language=normalize_language(str(payload.get("language", ""))))

    def save_language(self, language: str) -> WorkstationSettings:
        normalized = language.strip().lower()
        if normalized not in SUPPORTED_LANGUAGES:
            raise ValueError(f"unsupported workstation language: {language}")
        settings = WorkstationSettings(language=normalized)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                json.dump(settings.to_dict(), handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
                temp_path = Path(handle.name)
            os.replace(temp_path, self.path)
            temp_path = None
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
        return settings
