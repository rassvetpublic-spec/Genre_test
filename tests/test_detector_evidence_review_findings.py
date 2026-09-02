from __future__ import annotations

import json

import pytest

from genre_test.detector_evidence import (
    DetectorEvidenceError,
    DetectorEvidenceSample,
    DetectorResult,
    ProcessingStep,
)


def _result(**overrides: object) -> DetectorResult:
    payload: dict[str, object] = {
        "detector_id": "detector-x",
        "detector_version": "2026.09",
        "tested_at_utc": "2026-09-02T01:05:00Z",
        "verdict": "not_detected",
        "verdict_semantics": {"meaning": "fixture verdict"},
        "raw_response": {"label": "fixture"},
        "score": 1,
        "confidence": 1,
    }
    payload.update(overrides)
    return DetectorResult(**payload)  # type: ignore[arg-type]


def _sample(**overrides: object) -> DetectorEvidenceSample:
    payload: dict[str, object] = {
        "source_sha256": "a" * 64,
        "evidence_audio_sha256": "b" * 64,
        "transformation_class": "experimental",
        "ground_truth_origin": "controlled fixture",
        "ground_truth_basis": "immutable fixture manifest",
        "ground_truth_confidence": "known",
        "created_at_utc": "2026-09-02T01:00:00Z",
        "processing_history": (
            ProcessingStep("fixture transform", "fixture-tool", "1", parameters={}),
        ),
        "detector_results": (_result(),),
        "environment": {"runtime": "fixture"},
        "reproduction_count": 1,
        "reproduction_status": "single",
    }
    payload.update(overrides)
    return DetectorEvidenceSample(**payload)  # type: ignore[arg-type]


def test_unicode_surrogates_fail_closed_before_identity_hashing() -> None:
    with pytest.raises(DetectorEvidenceError, match="surrogate"):
        _sample(source_label="bad\ud800text")

    with pytest.raises(DetectorEvidenceError, match="surrogate"):
        _sample(environment={"value": "bad\udffftext"})

    with pytest.raises(DetectorEvidenceError, match="surrogate"):
        _sample(environment={"bad\ud800key": "value"})


def test_timestamp_precision_beyond_microseconds_is_rejected() -> None:
    with pytest.raises(DetectorEvidenceError, match="at most 6 digits"):
        _sample(created_at_utc="2026-09-02T01:00:00.1234567Z")

    with pytest.raises(DetectorEvidenceError, match="at most 6 digits"):
        _result(tested_at_utc="2026-09-02T01:05:00.1234569Z")

    preserved = _sample(created_at_utc="2026-09-02T01:00:00.123456Z")
    assert preserved.created_at_utc == "2026-09-02T01:00:00.123456Z"


def test_large_integer_score_is_preserved_exactly_in_canonical_evidence() -> None:
    exact_score = 9_007_199_254_740_993
    result = _result(score=exact_score)
    sample = _sample(detector_results=(result,))

    assert result.score == exact_score
    assert sample.to_dict()["detector_results"][0]["score"] == exact_score
    decoded = json.loads(sample.canonical_json())
    assert decoded["detector_results"][0]["score"] == exact_score


def test_non_json_numeric_score_types_and_non_finite_values_fail_closed() -> None:
    with pytest.raises(DetectorEvidenceError, match="JSON number"):
        _result(score="0.5")
    with pytest.raises(DetectorEvidenceError, match="JSON number"):
        _result(score=True)
    with pytest.raises(DetectorEvidenceError, match="finite"):
        _result(score=float("inf"))


def test_reproduction_status_and_count_invariants_are_consistent() -> None:
    with pytest.raises(DetectorEvidenceError, match="single.*== 1"):
        _sample(reproduction_count=2, reproduction_status="single")
    with pytest.raises(DetectorEvidenceError, match="reproduced.*>= 2"):
        _sample(reproduction_count=1, reproduction_status="reproduced")
    with pytest.raises(DetectorEvidenceError, match="not_reproduced.*>= 2"):
        _sample(reproduction_count=1, reproduction_status="not_reproduced")

    assert _sample(reproduction_count=2, reproduction_status="reproduced").reproduction_count == 2
    assert (
        _sample(reproduction_count=2, reproduction_status="not_reproduced").reproduction_count
        == 2
    )


def test_schema_version_requires_actual_non_boolean_integer() -> None:
    payload = _sample().to_dict()
    payload["schema_version"] = True
    with pytest.raises(DetectorEvidenceError, match="schema_version"):
        DetectorEvidenceSample.from_dict(payload)

    payload = _sample().to_dict()
    payload["schema_version"] = 1.0
    with pytest.raises(DetectorEvidenceError, match="schema_version"):
        DetectorEvidenceSample.from_dict(payload)
