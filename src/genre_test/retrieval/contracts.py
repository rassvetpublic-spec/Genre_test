from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Literal

RetrievalStatus = Literal["OK", "WARN", "FAIL", "N/A"]
EmbeddingScope = Literal["full", "segment", "representative", "text"]


@dataclass(frozen=True)
class RetrievalBackendInfo:
    backend_name: str
    backend_version: str
    clamp_code_revision: str | None
    clamp_weight_name: str | None
    clamp_weight_sha256: str | None
    mert_model_id: str | None
    mert_revision: str | None
    text_model_id: str | None
    text_model_revision: str | None
    text_tokenizer_revision: str | None
    preprocessing_version: str
    embedding_dim: int
    normalization: str = "l2"

    def __post_init__(self) -> None:
        if not self.backend_name.strip():
            raise ValueError("backend_name must not be empty")
        if not self.backend_version.strip():
            raise ValueError("backend_version must not be empty")
        if self.embedding_dim <= 0:
            raise ValueError("embedding_dim must be positive")
        if self.normalization != "l2":
            raise ValueError("v0.5 retrieval baseline requires l2 normalization")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(
            self.to_dict(),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class EmbeddingIdentity:
    backend_fingerprint: str
    scope: EmbeddingScope
    track_id: str | None = None
    text_sha256: str | None = None
    language: str | None = None
    start_s: float | None = None
    end_s: float | None = None

    def __post_init__(self) -> None:
        if not self.backend_fingerprint.strip():
            raise ValueError("backend_fingerprint must not be empty")
        if self.scope == "text":
            if not self.text_sha256:
                raise ValueError("text embeddings require text_sha256")
            if self.track_id is not None:
                raise ValueError("text embeddings cannot carry track_id")
        else:
            if not self.track_id:
                raise ValueError("audio embeddings require track_id")
            if self.text_sha256 is not None:
                raise ValueError("audio embeddings cannot carry text_sha256")
            if self.language is not None:
                raise ValueError("audio embeddings cannot carry language")

        segment_values = (self.start_s, self.end_s)
        if self.scope in {"segment", "representative"}:
            if any(value is None for value in segment_values):
                raise ValueError("segment embeddings require start_s and end_s")
            assert self.start_s is not None
            assert self.end_s is not None
            if self.start_s < 0 or self.end_s <= self.start_s:
                raise ValueError("segment bounds must satisfy 0 <= start_s < end_s")
        elif any(value is not None for value in segment_values):
            raise ValueError("full/text embeddings cannot carry segment bounds")

    @classmethod
    def for_text(
        cls,
        backend_fingerprint: str,
        text: str,
        *,
        language: str | None = None,
    ) -> EmbeddingIdentity:
        normalized = text.strip()
        if not normalized:
            raise ValueError("text query must not be empty")
        normalized_language = language.strip().lower() if language and language.strip() else None
        text_sha256 = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return cls(
            backend_fingerprint=backend_fingerprint,
            scope="text",
            text_sha256=text_sha256,
            language=normalized_language,
        )

    @property
    def cache_key(self) -> str:
        payload = json.dumps(
            asdict(self),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class EmbeddingVector:
    identity: EmbeddingIdentity
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError("embedding vector must not be empty")
        if not all(math.isfinite(value) for value in self.values):
            raise ValueError("embedding vector must contain only finite values")
        norm = math.sqrt(sum(value * value for value in self.values))
        if not math.isclose(norm, 1.0, rel_tol=1e-5, abs_tol=1e-5):
            raise ValueError(f"embedding vector must be L2 normalized, got norm={norm:.8f}")

    @classmethod
    def normalized(
        cls,
        identity: EmbeddingIdentity,
        values: list[float] | tuple[float, ...],
        *,
        expected_dim: int | None = None,
    ) -> EmbeddingVector:
        vector = tuple(float(value) for value in values)
        if not vector:
            raise ValueError("embedding vector must not be empty")
        if expected_dim is not None and len(vector) != expected_dim:
            raise ValueError(
                f"embedding dimension mismatch: expected {expected_dim}, got {len(vector)}"
            )
        if not all(math.isfinite(value) for value in vector):
            raise ValueError("embedding vector must contain only finite values")
        norm = math.sqrt(sum(value * value for value in vector))
        if norm <= 0.0:
            raise ValueError("embedding vector norm must be positive")
        normalized = tuple(value / norm for value in vector)
        return cls(identity=identity, values=normalized)

    @property
    def dimension(self) -> int:
        return len(self.values)


@dataclass(frozen=True)
class RetrievalHealth:
    status: RetrievalStatus
    value: str
    details: str
    backend_name: str = "CLaMP 3"


@dataclass(frozen=True)
class SearchHit:
    rank: int
    track_id: str
    path: str
    similarity: float
    backend_fingerprint: str

    def __post_init__(self) -> None:
        if self.rank <= 0:
            raise ValueError("rank must be positive")
        if not self.track_id.strip():
            raise ValueError("track_id must not be empty")
        if not self.path.strip():
            raise ValueError("path must not be empty")
        if not math.isfinite(self.similarity):
            raise ValueError("similarity must be finite")
        if self.similarity < -1.000001 or self.similarity > 1.000001:
            raise ValueError("cosine similarity must be in [-1, 1]")
        if not self.backend_fingerprint.strip():
            raise ValueError("backend_fingerprint must not be empty")
