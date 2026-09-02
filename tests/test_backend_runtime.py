from __future__ import annotations

import subprocess
import sys

import pytest

from genre_test.backend_runtime import (
    BackendCapabilities,
    BackendHealth,
    BackendIdentity,
    BackendPreflight,
    BackendRuntimeError,
    ExecutionEvidence,
)


def test_backend_identity_requires_model_id_for_model_revision() -> None:
    identity = BackendIdentity(
        backend_id="separator",
        backend_version="1.2.3",
        model_id="model-x",
        model_revision="sha256:fixture",
    )
    assert identity.to_dict()["model_id"] == "model-x"

    with pytest.raises(BackendRuntimeError, match="model_revision requires model_id"):
        BackendIdentity(
            backend_id="separator",
            backend_version="1.2.3",
            model_revision="revision-only",
        )


def test_degraded_or_unavailable_health_requires_reason() -> None:
    assert BackendHealth("available").to_dict() == {
        "state": "available",
        "reason": None,
    }
    assert BackendHealth("degraded", "CUDA unavailable").reason == "CUDA unavailable"

    with pytest.raises(BackendRuntimeError, match="requires a reason"):
        BackendHealth("unavailable")


def test_capabilities_require_unique_known_providers() -> None:
    capabilities = BackendCapabilities(
        providers=("cuda", "cpu"),
        dtypes=("float16", "float32"),
        supports_cancel=True,
    )
    assert capabilities.to_dict()["providers"] == ["cuda", "cpu"]

    with pytest.raises(BackendRuntimeError, match="duplicates"):
        BackendCapabilities(providers=("cuda", "cuda"))

    with pytest.raises(BackendRuntimeError, match="unsupported"):
        BackendCapabilities(providers=("quantum",))  # type: ignore[arg-type]


def test_execution_evidence_records_exact_requested_and_actual_provider() -> None:
    evidence = ExecutionEvidence(
        requested_provider="cuda",
        actual_provider="cuda",
        requested_dtype="float16",
        actual_dtype="float16",
        device_name="NVIDIA RTX fixture",
    )
    assert evidence.used_fallback is False
    assert evidence.to_dict() == {
        "requested_provider": "cuda",
        "actual_provider": "cuda",
        "used_fallback": False,
        "requested_dtype": "float16",
        "actual_dtype": "float16",
        "device_name": "NVIDIA RTX fixture",
    }


def test_provider_fallback_without_reason_fails_closed() -> None:
    with pytest.raises(BackendRuntimeError, match="silent fallback is forbidden"):
        ExecutionEvidence(
            requested_provider="cuda",
            actual_provider="cpu",
        )

    evidence = ExecutionEvidence(
        requested_provider="cuda",
        actual_provider="cpu",
        fallback_reason="CUDA backend failed preflight; explicit CPU fallback approved",
    )
    assert evidence.used_fallback is True
    assert evidence.to_dict()["fallback_reason"] == (
        "CUDA backend failed preflight; explicit CPU fallback approved"
    )


def test_dtype_fallback_without_reason_fails_closed() -> None:
    with pytest.raises(BackendRuntimeError, match="silent fallback is forbidden"):
        ExecutionEvidence(
            requested_provider="cuda",
            actual_provider="cuda",
            requested_dtype="float16",
            actual_dtype="float32",
        )

    evidence = ExecutionEvidence(
        requested_provider="cuda",
        actual_provider="cuda",
        requested_dtype="float16",
        actual_dtype="float32",
        fallback_reason="backend requires float32 on this device",
    )
    assert evidence.used_fallback is True


def test_requested_dtype_may_not_disappear_silently() -> None:
    with pytest.raises(BackendRuntimeError, match="silent fallback is forbidden"):
        ExecutionEvidence(
            requested_provider="cuda",
            actual_provider="cuda",
            requested_dtype="bfloat16",
            actual_dtype=None,
        )


def test_fallback_reason_is_rejected_when_nothing_changed() -> None:
    with pytest.raises(BackendRuntimeError, match="only valid"):
        ExecutionEvidence(
            requested_provider="cpu",
            actual_provider="cpu",
            fallback_reason="not actually a fallback",
        )


def test_preflight_rejects_provider_not_declared_by_backend() -> None:
    identity = BackendIdentity("repair", "1")
    capabilities = BackendCapabilities(providers=("cpu",), dtypes=("float32",))
    health = BackendHealth("available")

    with pytest.raises(BackendRuntimeError, match="requested_provider"):
        BackendPreflight(
            identity=identity,
            health=health,
            capabilities=capabilities,
            requested_provider="cuda",
        )

    with pytest.raises(BackendRuntimeError, match="requested_dtype"):
        BackendPreflight(
            identity=identity,
            health=health,
            capabilities=capabilities,
            requested_provider="cpu",
            requested_dtype="float16",
        )


def test_preflight_is_serializable_without_loading_backend() -> None:
    preflight = BackendPreflight(
        identity=BackendIdentity(
            backend_id="stem-reference",
            backend_version="2",
            model_id="fixture-model",
            model_revision="abc123",
        ),
        health=BackendHealth("available"),
        capabilities=BackendCapabilities(
            providers=("cuda", "cpu"),
            dtypes=("float16", "float32"),
        ),
        requested_provider="cuda",
        requested_dtype="float16",
    )
    payload = preflight.to_dict()
    assert payload["requested_provider"] == "cuda"
    assert payload["identity"]["backend_id"] == "stem-reference"
    assert payload["capabilities"]["providers"] == ["cuda", "cpu"]


def test_runtime_contract_import_has_no_heavy_model_side_effects() -> None:
    code = r'''
import sys
import genre_test.backend_runtime
forbidden = ("torch", "transformers", "librosa", "genre_test.retrieval")
loaded = sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + ".") for prefix in forbidden)
)
if loaded:
    raise SystemExit("unexpected heavy imports: " + ", ".join(loaded))
'''
    completed = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
