from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from .contracts import EmbeddingVector, RetrievalBackendInfo, RetrievalHealth


@runtime_checkable
class RetrievalBackend(Protocol):
    @property
    def info(self) -> RetrievalBackendInfo:
        """Return immutable model/preprocessing identity for this backend."""

    def health(self) -> RetrievalHealth:
        """Return backend health without forcing a model download."""

    def embed_audio(
        self,
        path: Path,
        *,
        track_id: str,
        start_s: float | None = None,
        end_s: float | None = None,
    ) -> EmbeddingVector:
        """Return one normalized audio embedding for a full track or explicit segment."""

    def embed_text(self, text: str, *, language: str | None = None) -> EmbeddingVector:
        """Return one normalized multilingual text embedding."""
