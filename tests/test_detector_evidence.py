from __future__ import annotations

import json
from dataclasses import replace

import pytest

from genre_test.detector_evidence import (
    EVIDENCE_SCHEMA,
    EVIDENCE_SCHEMA_VERSION,
    DetectorEvidenceError,
    DetectorEvidenceSample,
    DetectorResult,
    EvidenceAttachment,
    ProcessingStep,
)


def _result(**overrides: object) -> DetectorResult:
    payload: dict[str, object] = {
        "detector_id": "detector-x",
        "detector_version": "2026.09",
        "tested_at_utc": "2026-09-02T01:05:00Z",
        "verdict": "not_detected",
        "verdict_semantics": {
            "rule": "detector-native",
            "meaning": "service did not classify the sample as generated",
        },
        "raw_response": {"label": "human", "nested": {"b": 2, "a": 1}},
        "score": -2.75,
        "confidence": 0.61,
        "service_id": "vendor-api",
        "service_version": "2026-09",
        "model_id": "detector-model",
        "model_revision": "rev-7",
    }
    payload.update(overrides)
    return DetectorResult(**payload)  # type: ignore[arg-type]


def _sample(**overrides: object) -> DetectorEvidenceSample:
    payload: dict[str, object] = {
        "source_sha256": "a" * 64,
        "evidence_audio_sha256": "b" * 64,
        "transformation_class": "experimental",
        "ground_truth_origin": "controlled-generated fixture",
        "ground_truth_basis": "project-owned generation manifest + immutable source hash",
        "ground_truth_confidence": "known",
        "created_at_utc": "2026-09-02T01:00:00Z",
        "processing_history": (
            ProcessingStep(
                operation="reference export",
                tool_id="fixture-renderer",
                tool_version="1.2.3",
                parameters={"sample_rate": 48000, "format": "wav"},
            ),
            ProcessingStep(
                operation="documented research transform",
                tool_id="research-tool",
                tool_version="4.5.6",
                parameters={"mode": "test", "values": [3, 2, 1]},
            ),
        ),
        "detector_results": (_result(),),
        "environment": {
            "os": "Windows 11",
            "runner": "Genre_test",
            "runtime": {"python": "3.13", "build": "fixture"},
        },
        "reproduction_count": 2,
        "reproduction_status": "reproduced",
        "attachments": (
            EvidenceAttachment(
                kind="raw_response",
                sha256="c" * 64,
                media_type="application/json",
                label="detector-x raw response",
            ),
        ),
        "disclosure_reference": "vendor-case-123",
        "source_label": "private fixture A",
    }
    payload.update(overrides)
    return DetectorEvidenceSample(**payload)  # type: ignore[arg-type]


def test_schema_round_trip_and_identity_are_deterministic() -> None:
    original = _sample()
    payload = original.to_dict()
    assert payload["schema"] == EVIDENCE_SCHEMA
    assert payload["schema_version"] == EVIDENCE_SCHEMA_VERSION
    assert payload["transformation_class"] == "experimental"
    restored = DetectorEvidenceSample.from_dict(json.loads(original.canonical_json()))
    assert restored.to_dict() == original.to_dict()
    assert restored.evidence_id == original.evidence_id


def test_object_key_order_does_not_change_identity_but_sequence_order_does() -> None:
    first = _sample(environment={"z": 1, "a": {"y": 2, "b": 3}})
    second = _sample(environment={"a": {"b": 3, "y": 2}, "z": 1})
    assert first.canonical_json() == second.canonical_json()
    assert first.evidence_id == second.evidence_id

    reversed_history = replace(first, processing_history=tuple(reversed(first.processing_history)))
    assert reversed_history.evidence_id != first.evidence_id


def test_unknown_fields_fail_closed_at_every_versioned_record_level() -> None:
    payload = _sample().to_dict()
    payload["future_field"] = "unexpected"
    with pytest.raises(DetectorEvidenceError, match="unknown fields"):
        DetectorEvidenceSample.from_dict(payload)

    payload = _sample().to_dict()
    payload["processing_history"][0]["future_field"] = True
    with pytest.raises(DetectorEvidenceError, match="unknown fields"):
        DetectorEvidenceSample.from_dict(payload)

    payload = _sample().to_dict()
    payload["detector_results"][0]["future_field"] = True
    with pytest.raises(DetectorEvidenceError, match="unknown fields"):
        DetectorEvidenceSample.from_dict(payload)

    payload = _sample().to_dict()
    payload["attachments"][0]["future_field"] = True
    with pytest.raises(DetectorEvidenceError, match="unknown fields"):
        DetectorEvidenceSample.from_dict(payload)


def test_changed_audio_requires_processing_lineage() -> None:
    with pytest.raises(DetectorEvidenceError, match="processing_history"):
        _sample(processing_history=())

    reference = _sample(
        evidence_audio_sha256="a" * 64,
        transformation_class="reference",
        processing_history=(),
    )
    assert reference.processing_history == ()


def test_detector_raw_response_and_verdict_semantics_are_mandatory() -> None:
    payload = _sample().to_dict()
    del payload["detector_results"][0]["raw_response"]
    with pytest.raises(DetectorEvidenceError, match="raw_response.*required"):
        DetectorEvidenceSample.from_dict(payload)

    payload = _sample().to_dict()
    del payload["detector_results"][0]["verdict_semantics"]
    with pytest.raises(DetectorEvidenceError, match="verdict_semantics.*required"):
        DetectorEvidenceSample.from_dict(payload)

    with pytest.raises(DetectorEvidenceError, match="non-empty JSON object"):
        _result(verdict_semantics={})


def test_service_and_model_revision_require_explicit_identity() -> None:
    with pytest.raises(DetectorEvidenceError, match="service_version requires service_id"):
        _result(service_id=None, service_version="v2")
    with pytest.raises(DetectorEvidenceError, match="model_revision requires model_id"):
        _result(model_id=None, model_revision="rev")


def test_transformation_and_detector_semantics_are_identity_bound() -> None:
    original = _sample()
    changed_class = replace(original, transformation_class="codec")
    assert changed_class.evidence_id != original.evidence_id

    changed_result = replace(
        original.detector_results[0],
        verdict_semantics={"rule": "threshold-v2", "threshold": 0.7},
    )
    changed = replace(original, detector_results=(changed_result,))
    assert changed.evidence_id != original.evidence_id


def test_evidence_is_deeply_immutable_after_construction() -> None:
    environment = {"runtime": {"providers": ["cuda", "cpu"]}}
    raw_response = {"nested": {"labels": ["human", "generated"]}}
    parameters = {"values": [1, 2, 3]}
    step = ProcessingStep("measure", "tool", "1", parameters=parameters)
    result = _result(raw_response=raw_response)
    sample = _sample(processing_history=(step,), detector_results=(result,), environment=environment)
    evidence_id = sample.evidence_id

    environment["runtime"]["providers"].append("mutated")
    raw_response["nested"]["labels"].append("mutated")
    parameters["values"].append(4)
    assert sample.evidence_id == evidence_id
    assert sample.to_dict()["environment"]["runtime"]["providers"] == ["cuda", "cpu"]
    assert sample.detector_results[0].to_dict()["raw_response"]["nested"]["labels"] == [
        "human",
        "generated",
    ]
    assert sample.processing_history[0].to_dict()["parameters"]["values"] == [1, 2, 3]

    with pytest.raises(TypeError):
        sample.environment["new"] = "value"  # type: ignore[index]
    with pytest.raises(TypeError):
        sample.detector_results[0].raw_response["new"] = 1  # type: ignore[index]


def test_to_dict_returns_detached_mutable_json_without_mutating_identity() -> None:
    sample = _sample()
    evidence_id = sample.evidence_id
    payload = sample.to_dict()
    payload["environment"]["runtime"]["python"] = "mutated"
    payload["detector_results"][0]["raw_response"]["nested"]["a"] = 999
    assert sample.evidence_id == evidence_id
    assert sample.to_dict()["environment"]["runtime"]["python"] == "3.13"


def test_hash_timestamp_score_and_confidence_validation() -> None:
    normalized = _sample(source_sha256="A" * 64)
    assert normalized.source_sha256 == "a" * 64
    with pytest.raises(DetectorEvidenceError, match="source_sha256"):
        _sample(source_sha256="abc")
    with pytest.raises(DetectorEvidenceError, match="UTC"):
        _sample(created_at_utc="2026-09-02T01:00:00+03:00")
    with pytest.raises(DetectorEvidenceError, match="finite"):
        _result(score=float("inf"))
    with pytest.raises(DetectorEvidenceError, match="confidence"):
        _result(confidence=1.01)


def test_reproduction_and_ground_truth_contracts_fail_closed() -> None:
    with pytest.raises(DetectorEvidenceError, match="reproduction_count"):
        _sample(reproduction_count=1, reproduction_status="reproduced")
    with pytest.raises(DetectorEvidenceError, match="ground_truth_confidence"):
        _sample(ground_truth_confidence="absolute-ish")
    with pytest.raises(DetectorEvidenceError, match="at least one"):
        _sample(detector_results=())


def test_wrong_schema_version_and_missing_environment_fail_closed() -> None:
    payload = _sample().to_dict()
    payload["schema"] = "other"
    with pytest.raises(DetectorEvidenceError, match="schema"):
        DetectorEvidenceSample.from_dict(payload)

    payload = _sample().to_dict()
    payload["schema_version"] = 999
    with pytest.raises(DetectorEvidenceError, match="schema_version"):
        DetectorEvidenceSample.from_dict(payload)

    payload = _sample().to_dict()
    del payload["environment"]
    with pytest.raises(DetectorEvidenceError, match="environment.*required"):
        DetectorEvidenceSample.from_dict(payload)


def test_attachment_is_hash_reference_not_embedded_binary() -> None:
    attachment = _sample().to_dict()["attachments"][0]
    assert attachment == {
        "kind": "raw_response",
        "sha256": "c" * 64,
        "media_type": "application/json",
        "label": "detector-x raw response",
    }
    assert "source_path" not in _sample().to_dict()
    assert "evidence_audio_path" not in _sample().to_dict()
