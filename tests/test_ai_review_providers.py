import importlib
import json
import sys
from pathlib import Path
from urllib.error import URLError

import pytest

_REPO_ROOT = str(Path(__file__).resolve().parents[1])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_config = importlib.import_module("tools.ai_review.config")
_errors = importlib.import_module("tools.ai_review.errors")
_factory = importlib.import_module("tools.ai_review.providers.factory")
_ollama = importlib.import_module("tools.ai_review.providers.ollama_provider")
ConfigurationError = _errors.ConfigurationError
ProviderError = _errors.ProviderError
OllamaProvider = _ollama.OllamaProvider
build_provider = _factory.build_provider
load_settings = _config.load_settings


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class FakeRawResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self.payload


def test_ollama_provider_posts_schema_constrained_non_streaming_request(monkeypatch):
    captured = {}
    structured = {"title": "ok"}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse({"response": json.dumps(structured)})

    monkeypatch.setattr(_ollama, "urlopen", fake_urlopen)
    provider = OllamaProvider(
        model="gpt-oss:20b",
        max_output_tokens=1024,
        host="http://127.0.0.1:11434/",
    )
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
    }

    result = provider.generate_json(
        instructions="system",
        input_text="input",
        schema=schema,
        schema_name="proposal",
    )

    assert result == structured
    assert captured["url"] == "http://127.0.0.1:11434/api/generate"
    assert captured["payload"]["model"] == "gpt-oss:20b"
    assert captured["payload"]["stream"] is False
    assert captured["payload"]["format"] == schema
    assert captured["payload"]["system"] == "system"
    assert captured["payload"]["options"]["temperature"] == 0
    assert captured["payload"]["options"]["num_predict"] == 1024
    assert "JSON Schema" in captured["payload"]["prompt"]


def test_ollama_provider_wraps_connection_failures(monkeypatch):
    def fail_urlopen(request, timeout):
        raise URLError("connection refused")

    monkeypatch.setattr(_ollama, "urlopen", fail_urlopen)
    provider = OllamaProvider(model="gpt-oss:20b", max_output_tokens=1024)

    with pytest.raises(ProviderError, match="connection refused"):
        provider.generate_json(
            instructions="system",
            input_text="input",
            schema={"type": "object"},
            schema_name="proposal",
        )


def test_ollama_provider_rejects_malformed_api_envelope(monkeypatch):
    monkeypatch.setattr(
        _ollama,
        "urlopen",
        lambda request, timeout: FakeRawResponse(b"not-json"),
    )
    provider = OllamaProvider(model="gpt-oss:20b", max_output_tokens=1024)

    with pytest.raises(ProviderError, match="API response was not valid JSON"):
        provider.generate_json(
            instructions="system",
            input_text="input",
            schema={"type": "object"},
            schema_name="proposal",
        )


def test_ollama_provider_rejects_non_object_structured_output(monkeypatch):
    monkeypatch.setattr(
        _ollama,
        "urlopen",
        lambda request, timeout: FakeResponse({"response": "[1, 2, 3]"}),
    )
    provider = OllamaProvider(model="gpt-oss:20b", max_output_tokens=1024)

    with pytest.raises(ProviderError, match="root must be an object"):
        provider.generate_json(
            instructions="system",
            input_text="input",
            schema={"type": "object"},
            schema_name="proposal",
        )


def test_building_ollama_provider_does_not_import_openai_provider(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    sys.modules.pop("tools.ai_review.providers.openai_provider", None)

    provider = build_provider(
        "ollama",
        model="gpt-oss:20b",
        max_output_tokens=1024,
        ollama_host="http://127.0.0.1:11434",
    )

    assert provider.name == "ollama"
    assert "tools.ai_review.providers.openai_provider" not in sys.modules


def test_default_config_selects_free_stack(tmp_path, monkeypatch):
    for name in (
        "AI_REVIEW_PRIMARY_PROVIDER",
        "AI_REVIEW_PRIMARY_MODEL",
        "AI_REVIEW_SECONDARY_PROVIDER",
        "AI_REVIEW_SECONDARY_MODEL",
        "AI_REVIEW_OLLAMA_HOST",
        "AI_REVIEW_MAX_OUTPUT_TOKENS",
        "AI_REVIEW_RUNS_DIR",
    ):
        monkeypatch.delenv(name, raising=False)

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        json.dumps(
            {
                "primary_provider": "ollama",
                "primary_model": "gpt-oss:20b",
                "secondary_provider": "gemini",
                "secondary_model": "gemini-3.7-flash",
                "ollama_host": "http://127.0.0.1:11434",
                "max_output_tokens": 4096,
                "runs_dir": "runs",
            }
        ),
        encoding="utf-8",
    )

    settings = load_settings(config_path)
    assert settings.primary_provider == "ollama"
    assert settings.primary_model == "gpt-oss:20b"
    assert settings.secondary_provider == "gemini"
    assert settings.secondary_model == "gemini-3.7-flash"


def test_new_role_env_can_override_legacy_openai_gemini_config(tmp_path, monkeypatch):
    config_path = tmp_path / "legacy-config.yaml"
    config_path.write_text(
        json.dumps(
            {
                "openai_model": "${OPENAI_MODEL}",
                "gemini_model": "${GEMINI_MODEL}",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setenv("AI_REVIEW_PRIMARY_PROVIDER", "ollama")
    monkeypatch.setenv("AI_REVIEW_PRIMARY_MODEL", "gpt-oss:20b")
    monkeypatch.setenv("AI_REVIEW_SECONDARY_PROVIDER", "gemini")
    monkeypatch.setenv("AI_REVIEW_SECONDARY_MODEL", "gemini-3.7-flash")

    settings = load_settings(config_path)

    assert settings.primary_provider == "ollama"
    assert settings.primary_model == "gpt-oss:20b"
    assert settings.secondary_provider == "gemini"
    assert settings.secondary_model == "gemini-3.7-flash"


def test_partial_role_env_override_preserves_legacy_defaults(tmp_path, monkeypatch):
    for name in (
        "AI_REVIEW_PRIMARY_PROVIDER",
        "AI_REVIEW_PRIMARY_MODEL",
        "AI_REVIEW_SECONDARY_PROVIDER",
        "AI_REVIEW_SECONDARY_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    config_path = tmp_path / "legacy-config.yaml"
    config_path.write_text(
        json.dumps(
            {
                "openai_model": "legacy-openai-model",
                "gemini_model": "legacy-gemini-model",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("AI_REVIEW_PRIMARY_MODEL", "override-openai-model")

    settings = load_settings(config_path)

    assert settings.primary_provider == "openai"
    assert settings.primary_model == "override-openai-model"
    assert settings.secondary_provider == "gemini"
    assert settings.secondary_model == "legacy-gemini-model"


def test_mixed_role_config_preserves_unmigrated_legacy_model(tmp_path, monkeypatch):
    for name in (
        "AI_REVIEW_PRIMARY_PROVIDER",
        "AI_REVIEW_PRIMARY_MODEL",
        "AI_REVIEW_SECONDARY_PROVIDER",
        "AI_REVIEW_SECONDARY_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    config_path = tmp_path / "mixed-config.yaml"
    config_path.write_text(
        json.dumps(
            {
                "primary_provider": "ollama",
                "primary_model": "gpt-oss:20b",
                "gemini_model": "legacy-gemini-model",
            }
        ),
        encoding="utf-8",
    )

    settings = load_settings(config_path)

    assert settings.primary_provider == "ollama"
    assert settings.primary_model == "gpt-oss:20b"
    assert settings.secondary_provider == "gemini"
    assert settings.secondary_model == "legacy-gemini-model"


def test_mixed_secondary_role_config_preserves_legacy_primary_model(tmp_path, monkeypatch):
    for name in (
        "AI_REVIEW_PRIMARY_PROVIDER",
        "AI_REVIEW_PRIMARY_MODEL",
        "AI_REVIEW_SECONDARY_PROVIDER",
        "AI_REVIEW_SECONDARY_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    config_path = tmp_path / "mixed-config.yaml"
    config_path.write_text(
        json.dumps(
            {
                "openai_model": "legacy-openai-model",
                "secondary_provider": "gemini",
                "secondary_model": "new-gemini-model",
            }
        ),
        encoding="utf-8",
    )

    settings = load_settings(config_path)

    assert settings.primary_provider == "openai"
    assert settings.primary_model == "legacy-openai-model"
    assert settings.secondary_provider == "gemini"
    assert settings.secondary_model == "new-gemini-model"


def test_config_accepts_openai_gemini_topology(tmp_path, monkeypatch):
    for name in (
        "AI_REVIEW_PRIMARY_PROVIDER",
        "AI_REVIEW_PRIMARY_MODEL",
        "AI_REVIEW_SECONDARY_PROVIDER",
        "AI_REVIEW_SECONDARY_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        json.dumps(
            {
                "primary_provider": "openai",
                "primary_model": "openai-test-model",
                "secondary_provider": "gemini",
                "secondary_model": "gemini-test-model",
            }
        ),
        encoding="utf-8",
    )

    settings = load_settings(config_path)
    assert settings.primary_provider == "openai"
    assert settings.secondary_provider == "gemini"


def test_config_rejects_identical_primary_and_secondary(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        json.dumps(
            {
                "primary_provider": "ollama",
                "primary_model": "same",
                "secondary_provider": "ollama",
                "secondary_model": "same",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="must differ"):
        load_settings(config_path)
