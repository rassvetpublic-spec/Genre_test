from __future__ import annotations

import hashlib
import math
from pathlib import Path

import pytest

from genre_test.retrieval import (
    DenseCosineIndex,
    EmbeddingIdentity,
    EmbeddingVector,
    RetrievalBackendInfo,
    RetrievalStore,
    SidecarProtocolError,
    SidecarRequest,
    SidecarResponse,
    decode_vector_f32,
    encode_vector_f32,
)


def _backend_info(*, version: str = "1") -> RetrievalBackendInfo:
    return RetrievalBackendInfo(
        backend_name="clamp3",
        backend_version=version,
        clamp_code_revision="9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8",
        clamp_weight_name="test-weight.pth",
        clamp_weight_sha256="a" * 64,
        mert_model_id="m-a-p/MERT-v1-95M",
        mert_revision="test-mert",
        text_model_id="xlm-roberta-base",
        text_model_revision="test-text",
        text_tokenizer_revision="test-tokenizer",
        preprocessing_version="mert24k-v1",
        embedding_dim=3,
    )


def _audio_vector(
    backend: RetrievalBackendInfo,
    track_id: str,
    values: tuple[float, float, float],
) -> EmbeddingVector:
    identity = EmbeddingIdentity(
        backend_fingerprint=backend.fingerprint,
        scope="full",
        track_id=track_id,
    )
    return EmbeddingVector.normalized(identity, values, expected_dim=3)


def test_contract_serialization_round_trip() -> None:
    backend = _backend_info()
    restored_backend = RetrievalBackendInfo.from_dict(backend.to_dict())
    assert restored_backend == backend
    assert restored_backend.fingerprint == backend.fingerprint

    vector = _audio_vector(backend, "track-1", (3.0, 4.0, 0.0))
    restored_vector = EmbeddingVector.from_dict(vector.to_dict())
    assert restored_vector.identity == vector.identity
    assert restored_vector.values == vector.values


def test_store_round_trip_and_cache_hit(tmp_path: Path) -> None:
    backend = _backend_info()
    store = RetrievalStore(tmp_path / "retrieval.sqlite3")
    vector = _audio_vector(backend, "track-1", (1.0, 0.0, 0.0))

    digest = store.put(vector, backend=backend, path=r"D:\music\one.wav")
    assert len(digest) == 64
    assert store.stats(backend_fingerprint=backend.fingerprint) == {
        "full": 1,
        "total": 1,
    }

    stored = store.get(vector.identity)
    assert stored is not None
    assert stored.identity == vector.identity
    assert stored.path == r"D:\music\one.wav"
    assert math.isclose(stored.vector.values[0], 1.0)


def test_changed_backend_identity_is_stale_not_overwritten(tmp_path: Path) -> None:
    first_backend = _backend_info(version="1")
    second_backend = _backend_info(version="2")
    store = RetrievalStore(tmp_path / "retrieval.sqlite3")

    first = _audio_vector(first_backend, "track-1", (1.0, 0.0, 0.0))
    second = _audio_vector(second_backend, "track-1", (0.0, 1.0, 0.0))
    store.put(first, backend=first_backend, path="same.wav")
    store.put(second, backend=second_backend, path="same.wav")

    assert store.stats(backend_fingerprint=first_backend.fingerprint)["total"] == 1
    assert store.stats(backend_fingerprint=second_backend.fingerprint)["total"] == 1
    assert store.get(first.identity) is not None
    assert store.get(second.identity) is not None


def test_corrupt_vector_is_detected_and_can_be_removed(tmp_path: Path) -> None:
    backend = _backend_info()
    store = RetrievalStore(tmp_path / "retrieval.sqlite3")
    vector = _audio_vector(backend, "track-1", (1.0, 0.0, 0.0))
    store.put(vector, backend=backend, path="one.wav")

    corrupt = b"\x00" * 12
    with store.connect() as connection:
        connection.execute(
            "UPDATE embeddings SET vector_blob = ? WHERE cache_key = ?",
            (corrupt, vector.identity.cache_key),
        )

    assert store.delete_corrupt() == 1
    assert store.get(vector.identity) is None


def test_exact_cosine_index_ranks_nearest_track(tmp_path: Path) -> None:
    backend = _backend_info()
    store = RetrievalStore(tmp_path / "retrieval.sqlite3")
    store.put(
        _audio_vector(backend, "a", (1.0, 0.0, 0.0)),
        backend=backend,
        path="a.wav",
    )
    store.put(
        _audio_vector(backend, "b", (0.8, 0.2, 0.0)),
        backend=backend,
        path="b.wav",
    )
    store.put(
        _audio_vector(backend, "c", (0.0, 1.0, 0.0)),
        backend=backend,
        path="c.wav",
    )

    index = DenseCosineIndex.from_store(store, backend_fingerprint=backend.fingerprint)
    query_identity = EmbeddingIdentity.for_text(
        backend.fingerprint,
        "энергичный трек",
        language="ru",
    )
    query = EmbeddingVector.normalized(query_identity, (1.0, 0.0, 0.0), expected_dim=3)
    hits = index.search(query, top_k=2)

    assert [hit.track_id for hit in hits] == ["a", "b"]
    assert hits[0].similarity >= hits[1].similarity


def test_sidecar_protocol_and_f32_transport_round_trip() -> None:
    values = (0.25, -0.5, 0.75)
    encoded = encode_vector_f32(values)
    decoded = decode_vector_f32(encoded)
    assert decoded == values

    request = SidecarRequest("health", "req-1", {"download": False})
    assert '"protocol":"1"' in request.to_json()

    response = SidecarResponse.from_json(
        '{"protocol":"1","request_id":"req-1","ok":true,"payload":{"status":"OK"}}'
    )
    assert response.ok
    assert response.payload["status"] == "OK"


def test_sidecar_response_rejects_non_boolean_ok() -> None:
    with pytest.raises(SidecarProtocolError, match="must be boolean"):
        SidecarResponse.from_json(
            '{"protocol":"1","request_id":"req-1","ok":"false","payload":{}}'
        )


def test_vector_digest_is_content_addressed(tmp_path: Path) -> None:
    backend = _backend_info()
    store = RetrievalStore(tmp_path / "retrieval.sqlite3")
    vector = _audio_vector(backend, "track-1", (1.0, 0.0, 0.0))
    digest = store.put(vector, backend=backend, path="one.wav")
    stored = store.get(vector.identity)
    assert stored is not None
    assert digest == stored.vector_sha256
    assert len(bytes.fromhex(digest)) == hashlib.sha256().digest_size
