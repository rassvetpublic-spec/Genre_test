from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..errors import ProviderError


class OllamaProvider:
    name = "ollama"

    def __init__(
        self,
        model: str,
        max_output_tokens: int,
        host: str = "http://127.0.0.1:11434",
        timeout_seconds: float = 600.0,
    ) -> None:
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.host = host.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def generate_json(
        self,
        *,
        instructions: str,
        input_text: str,
        schema: dict[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        schema_json = json.dumps(schema, ensure_ascii=False, sort_keys=True)
        prompt = (
            f"{input_text.rstrip()}\n\n"
            f"Return exactly one JSON object for schema {schema_name!r}. "
            "Do not add markdown or commentary. The object must match this JSON Schema:\n"
            f"{schema_json}"
        )
        payload = {
            "model": self.model,
            "system": instructions,
            "prompt": prompt,
            "format": schema,
            "stream": False,
            "options": {
                "temperature": 0,
                "num_predict": self.max_output_tokens,
            },
        }
        request = Request(
            f"{self.host}/api/generate",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            detail = detail[:500].strip()
            suffix = f": {detail}" if detail else ""
            raise ProviderError(f"Ollama API call failed: HTTP {exc.code}{suffix}") from exc
        except URLError as exc:
            raise ProviderError(f"Ollama API call failed: {exc.reason}") from exc
        except OSError as exc:
            raise ProviderError(f"Ollama API call failed: {exc}") from exc

        try:
            envelope = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ProviderError("Ollama API response was not valid JSON.") from exc
        if not isinstance(envelope, dict):
            raise ProviderError("Ollama API response root must be an object.")

        output_text = envelope.get("response")
        if not isinstance(output_text, str) or not output_text.strip():
            raise ProviderError("Ollama API response contained no structured response text.")

        try:
            value = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ProviderError("Ollama structured output was not valid JSON.") from exc
        if not isinstance(value, dict):
            raise ProviderError("Ollama structured output root must be an object.")
        return value
