from __future__ import annotations

from .base import StructuredProvider
from ..errors import ConfigurationError


_SUPPORTED_PROVIDERS = {"ollama", "openai", "gemini"}


def build_provider(
    provider_name: str,
    *,
    model: str,
    max_output_tokens: int,
    ollama_host: str,
) -> StructuredProvider:
    name = provider_name.strip().lower()
    if name not in _SUPPORTED_PROVIDERS:
        supported = ", ".join(sorted(_SUPPORTED_PROVIDERS))
        raise ConfigurationError(
            f"Unsupported AI review provider {provider_name!r}. Supported: {supported}."
        )

    if name == "ollama":
        from .ollama_provider import OllamaProvider

        return OllamaProvider(
            model=model,
            max_output_tokens=max_output_tokens,
            host=ollama_host,
        )

    if name == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider(model=model, max_output_tokens=max_output_tokens)

    from .gemini_provider import GeminiProvider

    return GeminiProvider(model=model)
