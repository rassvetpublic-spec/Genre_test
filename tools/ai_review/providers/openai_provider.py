from __future__ import annotations

import json
import os
from typing import Any

from ..errors import ConfigurationError, ProviderError


class OpenAIProvider:
    name = "openai"

    def __init__(self, model: str, max_output_tokens: int) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ConfigurationError(
                "OPENAI_API_KEY is not set. Set it in the current process environment."
            )
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ConfigurationError(
                'OpenAI SDK is not installed. Run: pip install -e ".[ai-review]"'
            ) from exc

        self.model = model
        self.max_output_tokens = max_output_tokens
        self._client = OpenAI(api_key=api_key)

    def generate_json(
        self,
        *,
        instructions: str,
        input_text: str,
        schema: dict[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        try:
            response = self._client.responses.create(
                model=self.model,
                instructions=instructions,
                input=input_text,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": schema_name,
                        "strict": True,
                        "schema": schema,
                    }
                },
                max_output_tokens=self.max_output_tokens,
                store=False,
            )
        except Exception as exc:
            raise ProviderError(f"OpenAI Responses API call failed: {exc}") from exc

        if getattr(response, "status", None) != "completed":
            raise ProviderError(
                f"OpenAI response did not complete: status={getattr(response, 'status', None)!r}"
            )

        output_text = getattr(response, "output_text", None)
        if not output_text:
            raise ProviderError("OpenAI response contained no output_text.")

        try:
            value = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ProviderError("OpenAI structured output was not valid JSON.") from exc
        if not isinstance(value, dict):
            raise ProviderError("OpenAI structured output root must be an object.")
        return value
