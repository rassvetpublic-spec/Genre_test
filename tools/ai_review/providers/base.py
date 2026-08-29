from __future__ import annotations

from typing import Any, Protocol


class StructuredProvider(Protocol):
    name: str

    def generate_json(
        self,
        *,
        instructions: str,
        input_text: str,
        schema: dict[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        """Return one structured object matching the supplied schema."""
