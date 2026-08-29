from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re

from .errors import ConfigurationError


_ENV_REF = re.compile(r"^\$\{([A-Z0-9_]+)\}$")
_SUPPORTED_PROVIDERS = {"ollama", "openai", "gemini"}


@dataclass(frozen=True)
class Settings:
    primary_provider: str
    primary_model: str
    secondary_provider: str
    secondary_model: str
    ollama_host: str
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


def _setting(
    raw: dict[str, object],
    *,
    key: str,
    env_name: str,
    default: object | None = None,
) -> object:
    if env_name in os.environ and os.environ[env_name]:
        return os.environ[env_name]
    value = raw.get(key, default)
    return _resolve_scalar(value, key)


def _normalize_provider(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{field_name} must resolve to a non-empty string.")
    provider = value.strip().lower()
    if provider not in _SUPPORTED_PROVIDERS:
        supported = ", ".join(sorted(_SUPPORTED_PROVIDERS))
        raise ConfigurationError(f"{field_name} must be one of: {supported}.")
    return provider


def _normalize_model(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{field_name} must resolve to a non-empty string.")
    return value.strip()


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

    # v0.1 compatibility for external config files using the original keys.
    # Translate legacy values into role defaults first, then apply each
    # AI_REVIEW_* override independently so partial overrides preserve the
    # untouched v0.1 provider/model values.
    legacy = (
        "primary_provider" not in raw
        and "primary_model" not in raw
        and "secondary_provider" not in raw
        and "secondary_model" not in raw
        and ("openai_model" in raw or "gemini_model" in raw)
    )
    if legacy:
        primary_provider_default: object = "openai"
        primary_model_default = raw.get("openai_model")
        secondary_provider_default: object = "gemini"
        secondary_model_default = raw.get("gemini_model")
    else:
        primary_provider_default = "ollama"
        primary_model_default = "gpt-oss:20b"
        secondary_provider_default = "gemini"
        secondary_model_default = "gemini-3.7-flash"

    primary_provider_value = _setting(
        raw,
        key="primary_provider",
        env_name="AI_REVIEW_PRIMARY_PROVIDER",
        default=primary_provider_default,
    )
    primary_model_value = _setting(
        raw,
        key="primary_model",
        env_name="AI_REVIEW_PRIMARY_MODEL",
        default=primary_model_default,
    )
    secondary_provider_value = _setting(
        raw,
        key="secondary_provider",
        env_name="AI_REVIEW_SECONDARY_PROVIDER",
        default=secondary_provider_default,
    )
    secondary_model_value = _setting(
        raw,
        key="secondary_model",
        env_name="AI_REVIEW_SECONDARY_MODEL",
        default=secondary_model_default,
    )

    primary_provider = _normalize_provider(primary_provider_value, "primary_provider")
    primary_model = _normalize_model(primary_model_value, "primary_model")
    secondary_provider = _normalize_provider(secondary_provider_value, "secondary_provider")
    secondary_model = _normalize_model(secondary_model_value, "secondary_model")

    if (primary_provider, primary_model) == (secondary_provider, secondary_model):
        raise ConfigurationError(
            "primary and secondary provider/model must differ for independent consultation."
        )

    ollama_host_value = _setting(
        raw,
        key="ollama_host",
        env_name="AI_REVIEW_OLLAMA_HOST",
        default="http://127.0.0.1:11434",
    )
    if not isinstance(ollama_host_value, str) or not ollama_host_value.strip():
        raise ConfigurationError("ollama_host must resolve to a non-empty string.")
    ollama_host = ollama_host_value.strip().rstrip("/")
    if not (ollama_host.startswith("http://") or ollama_host.startswith("https://")):
        raise ConfigurationError("ollama_host must start with http:// or https://.")

    max_output_tokens = int(
        os.getenv("AI_REVIEW_MAX_OUTPUT_TOKENS", raw.get("max_output_tokens", 4096))
    )
    runs_dir = Path(
        os.getenv("AI_REVIEW_RUNS_DIR", str(raw.get("runs_dir", "tools/ai_review/runs")))
    )
    if max_output_tokens < 256:
        raise ConfigurationError("max_output_tokens must be at least 256.")

    return Settings(
        primary_provider=primary_provider,
        primary_model=primary_model,
        secondary_provider=secondary_provider,
        secondary_model=secondary_model,
        ollama_host=ollama_host,
        max_output_tokens=max_output_tokens,
        runs_dir=runs_dir,
    )
