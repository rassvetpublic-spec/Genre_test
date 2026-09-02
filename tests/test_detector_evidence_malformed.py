from __future__ import annotations

import pytest

from genre_test.detector_evidence import (
    DetectorEvidenceError,
    DetectorEvidenceSample,
    DetectorResult,
    EVIDENCE_SCHEMA,
    EVIDENCE_SCHEMA_VERSION,
    ProcessingStep,
)


VERDICT_SEMANTICS = {
    "rule": "fixture",
    "meaning": "fixture verdict semantics",
}


def _payload() -> dict[str, object]:
    return {
        "schema": EVIDENCE_SCHEMA,
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "source_sha256": "a" * 64,
        "evidence_audio_sha256": "b" * 64,
        "transformation_class": "controlled_test",
        "ground_truth_origin": "controlled fixture",
        "ground_truth_basis": "project-owned manifest",
        "ground_truth_confidence": "known",
        "created_at_utc": "2026-09-02T01:00:00Z",
        "processing_history": [
            {
                "operation": "reference export",
                "tool_id": "fixture",
                "tool_version": "1",
                "parameters": {},
            }
        ],
        "detector_results": [
            {
                "detector_id": "detector-x",
                "detector_version": "1",
                "tested_at_utc": "2026-09-02T01:05:00Z",
                "verdict": "not_detected",
                "verdict_semantics": VERDICT_SEMANTICS,
                "raw_response": {},
            }
        ],
        "environment": {},
        "reproduction_count": 1,
        "reproduction_status": "single",
        "attachments": [],
    }


def test_mixed_json_object_keys_fail_with_contract_error() -> None:
    with pytest.raises(DetectorEvidenceError, match="object keys"):
        ProcessingStep(
            operation="measure",
            tool_id="fixture",
            tool_version="1",
            parameters={"valid": 1, 2: "invalid"},  # type: ignore[dict-item]
        )


def test_non_mapping_top_level_payload_fails_closed() -> None:
    with pytest.raises(DetectorEvidenceError, match="evidence sample"):
        DetectorEvidenceSample.from_dict([])


def test_non_mapping_processing_record_fails_closed() -> None:
    payload = _payload()
    payload["processing_history"] = ["not-an-object"]

    with pytest.raises(DetectorEvidenceError, match="processing_history item"):
        DetectorEvidenceSample.from_dict(payload)


def test_non_mapping_detector_record_fails_closed() -> None:
    payload = _payload()
    payload["detector_results"] = [17]

    with pytest.raises(DetectorEvidenceError, match="detector_results item"):
        DetectorEvidenceSample.from_dict(payload)


def test_non_mapping_attachment_record_fails_closed() -> None:
    payload = _payload()
    payload["attachments"] = [None]

    with pytest.raises(DetectorEvidenceError, match="attachments item"):
        DetectorEvidenceSample.from_dict(payload)


def test_string_where_array_expected_fails_closed() -> None:
    payload = _payload()
    payload["detector_results"] = "detector-x"

    with pytest.raises(DetectorEvidenceError, match="detector_results must be an array"):
        DetectorEvidenceSample.from_dict(payload)


def test_boolean_score_is_rejected_as_non_numeric_evidence() -> None:
    with pytest.raises(DetectorEvidenceError, match="detector.score"):
        DetectorResult(
            detector_id="detector-x",
            detector_version="1",
            tested_at_utc="2026-09-02T01:05:00Z",
            verdict="unknown",
            verdict_semantics=VERDICT_SEMANTICS,
            raw_response={},
            score=True,
        )


def test_non_numeric_confidence_is_contract_error() -> None:
    with pytest.raises(DetectorEvidenceError, match="detector.confidence"):
        DetectorResult(
            detector_id="detector-x",
            detector_version="1",
            tested_at_utc="2026-09-02T01:05:00Z",
            verdict="unknown",
            verdict_semantics=VERDICT_SEMANTICS,
            raw_response={},
            confidence="high",  # type: ignore[arg-type]
        )
