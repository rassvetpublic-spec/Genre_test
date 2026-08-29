from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re

from .errors import ConfigurationError


_ENV_REF = re.compile(r"^\$\{([A-Z0-9_]+)\}$")


@dataclass(frozen=True)
class Settings:
    openai_model: str
    gemini_model: str
    max_output_tokens: int
    runs_dir: Path


def _resolve_scalar(value: object, field_name: str) -> object:
    if not isinstance(value, str):
        return value
    match = _ENV_REF.match(value)
    if not match:
        return value
    env_name = match.group(1)
    resolved = os.getenv(env_name)
    if not resolved:
        raise ConfigurationError(
            f"{field_name} requires environment variable {env_name}. "
            f"Set {env_name} or replace the placeholder in config.yaml."
        )
    return resolved


def load_settings(path: str | Path | None = None) -> Settings:
    config_path = (
        Path(path)
        if path is not None
        else Path(__file__).resolve().with_name("config.yaml")
    )
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigurationError(f"Config file not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            "config.yaml uses JSON-compatible YAML for a zero-dependency loader; "
            f"invalid JSON/YAML syntax in {config_path}: {exc}"
        ) from exc

    if not isinstance(raw, dict):
        raise ConfigurationError("config.yaml root must be an object.")

    openai_model = _resolve_scalar(raw.get("openai_model"), "openai_model")
    gemini_model = _resolve_scalar(raw.get("gemini_model"), "gemini_model")
    max_output_tokens = int(
        os.getenv("AI_REVIEW_MAX_OUTPUT_TOKENS", raw.get("max_output_tokens", 4096))
    )
    runs_dir = Path(
        os.getenv("AI_REVIEW_RUNS_DIR", str(raw.get("runs_dir", "tools/ai_review/runs")))
    )

    if not isinstance(openai_model, str) or not openai_model.strip():
        raise ConfigurationError("openai_model must resolve to a non-empty string.")
    if not isinstance(gemini_model, str) or not gemini_model.strip():
        raise ConfigurationError("gemini_model must resolve to a non-empty string.")
    if max_output_tokens < 256:
        raise ConfigurationError("max_output_tokens must be at least 256.")

    return Settings(
        openai_model=openai_model.strip(),
        gemini_model=gemini_model.strip(),
        max_output_tokens=max_output_tokens,
        runs_dir=runs_dir,
    )
