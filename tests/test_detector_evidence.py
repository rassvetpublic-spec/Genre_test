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


def _sample(**overrides: object) -> DetectorEvidenceSample:
    payload: dict[str, object] = {
        "source_sha256": "a" * 64,
        "evidence_audio_sha256": "b" * 64,
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
                note="ordered processing history is evidence and must not be rewritten",
            ),
        ),
        "detector_results": (
            DetectorResult(
                detector_id="detector-x",
                detector_version="2026.09",
                tested_at_utc="2026-09-02T01:05:00+00:00",
                verdict="not_detected",
                raw_response={"label": "human", "nested": {"b": 2, "a": 1}},
                score=-2.75,
                confidence=0.61,
            ),
        ),
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


def test_schema_identity_and_required_lineage_are_serialized() -> None:
    data = _sample().to_dict()

    assert data["schema"] == EVIDENCE_SCHEMA
    assert data["schema_version"] == EVIDENCE_SCHEMA_VERSION
    assert data["source_sha256"] == "a" * 64
    assert data["evidence_audio_sha256"] == "b" * 64
    assert data["ground_truth_confidence"] == "known"
    assert len(data["processing_history"]) == 2
    assert len(data["detector_results"]) == 1


def test_processing_history_order_is_preserved_exactly() -> None:
    data = _sample().to_dict()

    assert [step["operation"] for step in data["processing_history"]] == [
        "reference export",
        "documented research transform",
    ]
    assert data["processing_history"][1]["parameters"]["values"] == [3, 2, 1]


def test_object_key_order_does_not_change_canonical_json_or_evidence_id() -> None:
    first = _sample(environment={"z": 1, "a": {"y": 2, "b": 3}})
    second = _sample(environment={"a": {"b": 3, "y": 2}, "z": 1})

    assert first.canonical_json() == second.canonical_json()
    assert first.evidence_id == second.evidence_id


def test_sequence_order_is_evidence_and_changes_identity() -> None:
    original = _sample()
    reversed_history = replace(original, processing_history=tuple(reversed(original.processing_history)))

    assert original.canonical_json() != reversed_history.canonical_json()
    assert original.evidence_id != reversed_history.evidence_id


def test_round_trip_preserves_canonical_identity() -> None:
    original = _sample()
    decoded = json.loads(original.canonical_json())
    restored = DetectorEvidenceSample.from_dict(decoded)

    assert restored.to_dict() == original.to_dict()
    assert restored.evidence_id == original.evidence_id


def test_hashes_are_normalized_and_must_be_sha256() -> None:
    sample = _sample(source_sha256="A" * 64)
    assert sample.source_sha256 == "a" * 64

    with pytest.raises(DetectorEvidenceError, match="source_sha256"):
        _sample(source_sha256="abc")


def test_detector_timestamp_is_normalized_to_utc_z() -> None:
    result = DetectorResult(
        detector_id="x",
        detector_version="1",
        tested_at_utc="2026-09-02T01:05:00+00:00",
        verdict="unknown",
        raw_response={},
    )

    assert result.tested_at_utc == "2026-09-02T01:05:00Z"


def test_non_utc_or_naive_timestamps_are_rejected() -> None:
    with pytest.raises(DetectorEvidenceError, match="UTC"):
        _sample(created_at_utc="2026-09-02T01:00:00+03:00")

    with pytest.raises(DetectorEvidenceError, match="UTC"):
        _sample(created_at_utc="2026-09-02T01:00:00")


def test_raw_score_is_not_forced_to_zero_one_but_confidence_is() -> None:
    result = DetectorResult(
        detector_id="x",
        detector_version="1",
        tested_at_utc="2026-09-02T01:05:00Z",
        verdict="unknown",
        raw_response={},
        score=-17.25,
        confidence=1.0,
    )
    assert result.score == -17.25

    with pytest.raises(DetectorEvidenceError, match="confidence"):
        replace(result, confidence=1.01)


def test_non_finite_values_are_rejected_from_evidence_json() -> None:
    with pytest.raises(DetectorEvidenceError, match="non-finite"):
        ProcessingStep(
            operation="measure",
            tool_id="tool",
            tool_version="1",
            parameters={"value": float("nan")},
        )

    with pytest.raises(DetectorEvidenceError, match="finite"):
        DetectorResult(
            detector_id="x",
            detector_version="1",
            tested_at_utc="2026-09-02T01:05:00Z",
            verdict="unknown",
            raw_response={},
            score=float("inf"),
        )


def test_detector_results_are_required() -> None:
    with pytest.raises(DetectorEvidenceError, match="at least one"):
        _sample(detector_results=())


def test_reproduced_status_requires_at_least_two_runs() -> None:
    with pytest.raises(DetectorEvidenceError, match="reproduction_count"):
        _sample(reproduction_count=1, reproduction_status="reproduced")

    pending = _sample(reproduction_count=1, reproduction_status="pending")
    assert pending.reproduction_status == "pending"


def test_unknown_ground_truth_confidence_value_is_rejected() -> None:
    with pytest.raises(DetectorEvidenceError, match="ground_truth_confidence"):
        _sample(ground_truth_confidence="absolute-ish")


def test_attachment_is_hash_reference_not_embedded_binary() -> None:
    data = _sample().to_dict()["attachments"][0]

    assert data == {
        "kind": "raw_response",
        "sha256": "c" * 64,
        "media_type": "application/json",
        "label": "detector-x raw response",
    }


def test_canonical_evidence_contains_no_implicit_local_source_path_field() -> None:
    data = _sample().to_dict()

    assert "source_path" not in data
    assert "evidence_audio_path" not in data
    assert data["source_label"] == "private fixture A"


def test_evidence_identity_changes_when_detector_result_changes() -> None:
    sample = _sample()
    changed_result = replace(sample.detector_results[0], verdict="detected")
    changed = replace(sample, detector_results=(changed_result,))

    assert sample.evidence_id != changed.evidence_id


def test_wrong_schema_or_version_fails_closed() -> None:
    payload = _sample().to_dict()
    payload["schema"] = "other"
    with pytest.raises(DetectorEvidenceError, match="schema"):
        DetectorEvidenceSample.from_dict(payload)

    payload = _sample().to_dict()
    payload["schema_version"] = 999
    with pytest.raises(DetectorEvidenceError, match="schema_version"):
        DetectorEvidenceSample.from_dict(payload)
