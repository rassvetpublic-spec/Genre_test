from __future__ import annotations

import math
from pathlib import Path

import pytest

from genre_test.retrieval import (
    EmbeddingIdentity,
    EmbeddingVector,
    RetrievalBackend,
    RetrievalBackendInfo,
    RetrievalHealth,
    detect_retrieval_health,
)


def _backend_info() -> RetrievalBackendInfo:
    return RetrievalBackendInfo(
        backend_name="clamp3",
        backend_version="spike-1",
        clamp_code_revision="9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8",
        clamp_weight_name="test-weight.pth",
        clamp_weight_sha256="a" * 64,
        mert_model_id="m-a-p/MERT-v1-95M",
        mert_revision="test-revision",
        preprocessing_version="mert24k-v1",
        embedding_dim=3,
    )


def test_backend_fingerprint_is_stable_and_content_addressed() -> None:
    first = _backend_info()
    second = _backend_info()

    assert first.fingerprint == second.fingerprint
    assert len(first.fingerprint) == 64

    changed = RetrievalBackendInfo(
        **{**first.to_dict(), "preprocessing_version": "mert24k-v2"}  # type: ignore[arg-type]
    )
    assert changed.fingerprint != first.fingerprint


def test_text_embedding_identity_supports_russian_unicode() -> None:
    identity = EmbeddingIdentity.for_text(
        _backend_info().fingerprint,
        "  мрачный кинематографичный электронный трек  ",
    )

    assert identity.scope == "text"
    assert identity.text_sha256 is not None
    assert len(identity.text_sha256) == 64
    assert len(identity.cache_key) == 64


def test_segment_identity_requires_valid_bounds() -> None:
    fingerprint = _backend_info().fingerprint

    with pytest.raises(ValueError, match="require start_s and end_s"):
        EmbeddingIdentity(
            backend_fingerprint=fingerprint,
            scope="segment",
            track_id="track-1",
        )

    with pytest.raises(ValueError, match="0 <= start_s < end_s"):
        EmbeddingIdentity(
            backend_fingerprint=fingerprint,
            scope="segment",
            track_id="track-1",
            start_s=30.0,
            end_s=10.0,
        )


def test_embedding_vector_normalizes_for_cosine_search() -> None:
    identity = EmbeddingIdentity(
        backend_fingerprint=_backend_info().fingerprint,
        scope="full",
        track_id="track-1",
    )
    vector = EmbeddingVector.normalized(identity, [3.0, 4.0, 0.0], expected_dim=3)

    assert vector.dimension == 3
    assert math.isclose(sum(value * value for value in vector.values), 1.0)


def test_embedding_vector_rejects_wrong_dimension() -> None:
    identity = EmbeddingIdentity(
        backend_fingerprint=_backend_info().fingerprint,
        scope="full",
        track_id="track-1",
    )

    with pytest.raises(ValueError, match="dimension mismatch"):
        EmbeddingVector.normalized(identity, [1.0, 2.0], expected_dim=3)


def test_retrieval_health_is_na_when_optional_runtime_is_not_configured() -> None:
    health = detect_retrieval_health({})

    assert health.status == "N/A"
    assert "ordinary Genre_test analysis remains available" in health.details


def test_retrieval_health_fails_for_missing_configured_interpreter(tmp_path: Path) -> None:
    missing = tmp_path / "missing-python.exe"
    health = detect_retrieval_health({"GENRE_TEST_CLAMP3_PYTHON": str(missing)})

    assert health.status == "FAIL"
    assert "does not exist" in health.details


def test_retrieval_health_warns_for_unverified_existing_interpreter(tmp_path: Path) -> None:
    interpreter = tmp_path / "python.exe"
    interpreter.write_bytes(b"")

    health = detect_retrieval_health({"GENRE_TEST_CLAMP3_PYTHON": str(interpreter)})

    assert health.status == "WARN"
    assert "protocol handshake is not implemented yet" in health.details


class _FakeBackend:
    @property
    def info(self) -> RetrievalBackendInfo:
        return _backend_info()

    def health(self) -> RetrievalHealth:
        return RetrievalHealth("OK", "fake", "test backend", backend_name="fake")

    def embed_audio(
        self,
        path: Path,
        *,
        track_id: str,
        start_s: float | None = None,
        end_s: float | None = None,
    ) -> EmbeddingVector:
        del path
        scope = "segment" if start_s is not None or end_s is not None else "full"
        identity = EmbeddingIdentity(
            backend_fingerprint=self.info.fingerprint,
            scope=scope,
            track_id=track_id,
            start_s=start_s,
            end_s=end_s,
        )
        return EmbeddingVector.normalized(identity, [1.0, 0.0, 0.0], expected_dim=3)

    def embed_text(self, text: str, *, language: str | None = None) -> EmbeddingVector:
        del language
        identity = EmbeddingIdentity.for_text(self.info.fingerprint, text)
        return EmbeddingVector.normalized(identity, [0.0, 1.0, 0.0], expected_dim=3)


def test_fake_backend_conforms_to_protocol() -> None:
    backend = _FakeBackend()

    assert isinstance(backend, RetrievalBackend)
    assert backend.embed_text("русский запрос", language="ru").dimension == 3
