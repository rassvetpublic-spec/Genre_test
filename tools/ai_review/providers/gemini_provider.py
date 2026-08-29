from __future__ import annotations

import json
import os
from typing import Any

from ..errors import ConfigurationError, ProviderError


class GeminiProvider:
    name = "gemini"

    def __init__(self, model: str) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ConfigurationError(
                "GEMINI_API_KEY is not set. Set it in the current process environment."
            )
        try:
            from google import genai
        except ImportError as exc:
            raise ConfigurationError(
                'Google GenAI SDK is not installed. Run: pip install -e ".[ai-review]"'
            ) from exc

        self.model = model
        self._client = genai.Client(api_key=api_key)

    def generate_json(
        self,
        *,
        instructions: str,
        input_text: str,
        schema: dict[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        del schema_name
        full_input = f"{instructions.strip()}\n\n{input_text}"
        try:
            interaction = self._client.interactions.create(
                model=self.model,
                input=full_input,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": schema,
                },
            )
        except Exception as exc:
            raise ProviderError(f"Gemini Interactions API call failed: {exc}") from exc

        output_text = getattr(interaction, "output_text", None)
        if not output_text:
            raise ProviderError("Gemini interaction contained no output_text.")

        try:
            value = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ProviderError("Gemini structured output was not valid JSON.") from exc
        if not isinstance(value, dict):
            raise ProviderError("Gemini structured output root must be an object.")
        return value
