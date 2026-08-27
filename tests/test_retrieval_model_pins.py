from __future__ import annotations

import hashlib

from genre_test.retrieval.model_pins import (
    CLAMP3_CODE_REVISION,
    CLAMP3_WEIGHT_SHA256,
    CLAMP3_WEIGHT_VARIANT,
    MERT_LICENSE,
    MERT_REVISION,
    PREPROCESSING_VERSION,
    RESAMPLER,
    TEXT_MODEL_REVISION,
    manifest_fingerprint,
    selected_model_manifest,
    sha256_file,
)


def test_selected_retrieval_manifest_is_explicit_and_stable() -> None:
    manifest = selected_model_manifest()

    assert CLAMP3_WEIGHT_VARIANT == "saas"
    assert manifest["clamp3"]["code_revision"] == CLAMP3_CODE_REVISION
    assert manifest["clamp3"]["weight_sha256"] == CLAMP3_WEIGHT_SHA256
    assert manifest["mert"]["revision"] == MERT_REVISION
    assert manifest["mert"]["license"] == MERT_LICENSE == "CC-BY-NC-4.0"
    assert manifest["text"]["revision"] == TEXT_MODEL_REVISION
    assert manifest["preprocessing"]["version"] == PREPROCESSING_VERSION
    assert manifest["preprocessing"]["target_sample_rate"] == 24_000
    assert manifest["preprocessing"]["resampler"] == RESAMPLER
    assert manifest["preprocessing"]["window_seconds"] == 5.0
    assert manifest["preprocessing"]["processor_normalize"] is True
    assert manifest["preprocessing"]["embedding_dimension"] == 768
    assert manifest["preprocessing"]["normalization"] == "l2"


def test_manifest_fingerprint_is_deterministic_sha256() -> None:
    first = manifest_fingerprint()
    second = manifest_fingerprint()

    assert first == second
    assert len(first) == 64
    int(first, 16)


def test_sha256_file(tmp_path) -> None:
    payload = b"genre-test-clamp3-pin-test\n"
    path = tmp_path / "sample.bin"
    path.write_bytes(payload)

    assert sha256_file(path) == hashlib.sha256(payload).hexdigest()
