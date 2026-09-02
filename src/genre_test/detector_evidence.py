from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

EVIDENCE_SCHEMA = "genre-test-detector-evidence-sample-v1"
EVIDENCE_SCHEMA_VERSION = 1

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GROUND_TRUTH_CONFIDENCE = frozenset({"known", "high", "medium", "low", "unknown"})
_REPRODUCTION_STATUS = frozenset({"single", "reproduced", "not_reproduced", "pending"})


class DetectorEvidenceError(ValueError):
    """Raised when detector evidence cannot satisfy the versioned contract."""


def _required_text(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DetectorEvidenceError(f"{field_name} must be a non-empty string")
    if "\x00" in value:
        raise DetectorEvidenceError(f"{field_name} must not contain NUL")
    return value.strip()


def _optional_text(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, field_name=field_name)


def _sha256(value: Any, *, field_name: str) -> str:
    normalized = _required_text(value, field_name=field_name).lower()
    if not _SHA256_RE.fullmatch(normalized):
        raise DetectorEvidenceError(f"{field_name} must be a 64-character SHA-256 hex digest")
    return normalized


def _utc_timestamp(value: Any, *, field_name: str) -> str:
    raw = _required_text(value, field_name=field_name)
    candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise DetectorEvidenceError(f"{field_name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise DetectorEvidenceError(f"{field_name} must be UTC")
    return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _record(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DetectorEvidenceError(f"{field_name} must be a JSON object")
    for key in value:
        if not isinstance(key, str) or not key:
            raise DetectorEvidenceError(f"{field_name} object keys must be non-empty strings")
    return value


def _array(value: Any, *, field_name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise DetectorEvidenceError(f"{field_name} must be an array")
    return value


def _json_value(value: Any, *, field_name: str) -> Any:
    """Return a detached JSON-compatible value with deterministic object key order."""

    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise DetectorEvidenceError(f"{field_name} contains a non-finite number")
        return value
    if isinstance(value, Mapping):
        record = _record(value, field_name=field_name)
        return {
            key: _json_value(record[key], field_name=f"{field_name}.{key}")
            for key in sorted(record)
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [
            _json_value(item, field_name=f"{field_name}[{index}]")
            for index, item in enumerate(value)
        ]
    raise DetectorEvidenceError(f"{field_name} contains a non-JSON-compatible value")


def _json_object(value: Any, *, field_name: str) -> dict[str, Any]:
    record = _record(value, field_name=field_name)
    normalized = _json_value(record, field_name=field_name)
    assert isinstance(normalized, dict)
    return normalized


def _finite_float(value: Any, *, field_name: str) -> float:
    if isinstance(value, bool):
        raise DetectorEvidenceError(f"{field_name} must be a finite number")
    try:
        normalized = float(value)
    except (TypeError, ValueError) as exc:
        raise DetectorEvidenceError(f"{field_name} must be a finite number") from exc
    if not math.isfinite(normalized):
        raise DetectorEvidenceError(f"{field_name} must be finite")
    return normalized


@dataclass(frozen=True)
class ProcessingStep:
    """One ordered, factual operation in the evidence sample processing history."""

    operation: str
    tool_id: str
    tool_version: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    note: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "operation",
            _required_text(self.operation, field_name="processing.operation"),
        )
        object.__setattr__(
            self,
            "tool_id",
            _required_text(self.tool_id, field_name="processing.tool_id"),
        )
        object.__setattr__(
            self,
            "tool_version",
            _required_text(self.tool_version, field_name="processing.tool_version"),
        )
        object.__setattr__(
            self,
            "parameters",
            _json_object(self.parameters, field_name="processing.parameters"),
        )
        object.__setattr__(
            self,
            "note",
            _optional_text(self.note, field_name="processing.note"),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "operation": self.operation,
            "tool_id": self.tool_id,
            "tool_version": self.tool_version,
            "parameters": _json_object(
                self.parameters,
                field_name="processing.parameters",
            ),
        }
        if self.note is not None:
            payload["note"] = self.note
        return payload

    @classmethod
    def from_dict(cls, payload: Any) -> ProcessingStep:
        record = _record(payload, field_name="processing_history item")
        return cls(
            operation=record.get("operation"),
            tool_id=record.get("tool_id"),
            tool_version=record.get("tool_version"),
            parameters=record.get("parameters", {}),
            note=record.get("note"),
        )


@dataclass(frozen=True)
class DetectorResult:
    """Raw result evidence for one detector/service/model identity at one time."""

    detector_id: str
    detector_version: str
    tested_at_utc: str
    verdict: str
    raw_response: Mapping[str, Any]
    score: float | None = None
    confidence: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "detector_id",
            _required_text(self.detector_id, field_name="detector.detector_id"),
        )
        object.__setattr__(
            self,
            "detector_version",
            _required_text(self.detector_version, field_name="detector.detector_version"),
        )
        object.__setattr__(
            self,
            "tested_at_utc",
            _utc_timestamp(self.tested_at_utc, field_name="detector.tested_at_utc"),
        )
        object.__setattr__(
            self,
            "verdict",
            _required_text(self.verdict, field_name="detector.verdict"),
        )
        object.__setattr__(
            self,
            "raw_response",
            _json_object(self.raw_response, field_name="detector.raw_response"),
        )
        if self.score is not None:
            object.__setattr__(
                self,
                "score",
                _finite_float(self.score, field_name="detector.score"),
            )
        if self.confidence is not None:
            confidence = _finite_float(self.confidence, field_name="detector.confidence")
            if confidence < 0.0 or confidence > 1.0:
                raise DetectorEvidenceError("detector.confidence must be between 0 and 1")
            object.__setattr__(self, "confidence", confidence)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "detector_id": self.detector_id,
            "detector_version": self.detector_version,
            "tested_at_utc": self.tested_at_utc,
            "verdict": self.verdict,
            "raw_response": _json_object(
                self.raw_response,
                field_name="detector.raw_response",
            ),
        }
        if self.score is not None:
            payload["score"] = self.score
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        return payload

    @classmethod
    def from_dict(cls, payload: Any) -> DetectorResult:
        record = _record(payload, field_name="detector_results item")
        return cls(
            detector_id=record.get("detector_id"),
            detector_version=record.get("detector_version"),
            tested_at_utc=record.get("tested_at_utc"),
            verdict=record.get("verdict"),
            raw_response=record.get("raw_response", {}),
            score=record.get("score"),
            confidence=record.get("confidence"),
        )


@dataclass(frozen=True)
class EvidenceAttachment:
    """Hash-only reference to retained logs, screenshots, reports, or other evidence."""

    kind: str
    sha256: str
    media_type: str
    label: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "kind",
            _required_text(self.kind, field_name="attachment.kind"),
        )
        object.__setattr__(
            self,
            "sha256",
            _sha256(self.sha256, field_name="attachment.sha256"),
        )
        object.__setattr__(
            self,
            "media_type",
            _required_text(self.media_type, field_name="attachment.media_type"),
        )
        object.__setattr__(
            self,
            "label",
            _optional_text(self.label, field_name="attachment.label"),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "kind": self.kind,
            "sha256": self.sha256,
            "media_type": self.media_type,
        }
        if self.label is not None:
            payload["label"] = self.label
        return payload

    @classmethod
    def from_dict(cls, payload: Any) -> EvidenceAttachment:
        record = _record(payload, field_name="attachments item")
        return cls(
            kind=record.get("kind"),
            sha256=record.get("sha256"),
            media_type=record.get("media_type"),
            label=record.get("label"),
        )


@dataclass(frozen=True)
class DetectorEvidenceSample:
    """Versioned evidence that binds ground truth, processing history, and detector outputs."""

    source_sha256: str
    evidence_audio_sha256: str
    ground_truth_origin: str
    ground_truth_basis: str
    ground_truth_confidence: str
    created_at_utc: str
    processing_history: tuple[ProcessingStep, ...]
    detector_results: tuple[DetectorResult, ...]
    environment: Mapping[str, Any]
    reproduction_count: int = 1
    reproduction_status: str = "single"
    attachments: tuple[EvidenceAttachment, ...] = ()
    disclosure_reference: str | None = None
    source_label: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_sha256",
            _sha256(self.source_sha256, field_name="source_sha256"),
        )
        object.__setattr__(
            self,
            "evidence_audio_sha256",
            _sha256(self.evidence_audio_sha256, field_name="evidence_audio_sha256"),
        )
        object.__setattr__(
            self,
            "ground_truth_origin",
            _required_text(self.ground_truth_origin, field_name="ground_truth_origin"),
        )
        object.__setattr__(
            self,
            "ground_truth_basis",
            _required_text(self.ground_truth_basis, field_name="ground_truth_basis"),
        )
        confidence = _required_text(
            self.ground_truth_confidence,
            field_name="ground_truth_confidence",
        ).lower()
        if confidence not in _GROUND_TRUTH_CONFIDENCE:
            allowed = ", ".join(sorted(_GROUND_TRUTH_CONFIDENCE))
            raise DetectorEvidenceError(
                f"ground_truth_confidence must be one of: {allowed}"
            )
        object.__setattr__(self, "ground_truth_confidence", confidence)
        object.__setattr__(
            self,
            "created_at_utc",
            _utc_timestamp(self.created_at_utc, field_name="created_at_utc"),
        )

        history = _array(self.processing_history, field_name="processing_history")
        if not all(isinstance(item, ProcessingStep) for item in history):
            raise DetectorEvidenceError(
                "processing_history must contain ProcessingStep values"
            )
        object.__setattr__(self, "processing_history", tuple(history))

        results = _array(self.detector_results, field_name="detector_results")
        if not results or not all(isinstance(item, DetectorResult) for item in results):
            raise DetectorEvidenceError(
                "detector_results must contain at least one DetectorResult"
            )
        object.__setattr__(self, "detector_results", tuple(results))
        object.__setattr__(
            self,
            "environment",
            _json_object(self.environment, field_name="environment"),
        )

        if (
            isinstance(self.reproduction_count, bool)
            or not isinstance(self.reproduction_count, int)
            or self.reproduction_count < 1
        ):
            raise DetectorEvidenceError("reproduction_count must be an integer >= 1")
        status = _required_text(
            self.reproduction_status,
            field_name="reproduction_status",
        ).lower()
        if status not in _REPRODUCTION_STATUS:
            allowed = ", ".join(sorted(_REPRODUCTION_STATUS))
            raise DetectorEvidenceError(f"reproduction_status must be one of: {allowed}")
        if status == "reproduced" and self.reproduction_count < 2:
            raise DetectorEvidenceError(
                "reproduced evidence requires reproduction_count >= 2"
            )
        object.__setattr__(self, "reproduction_status", status)

        attachments = _array(self.attachments, field_name="attachments")
        if not all(isinstance(item, EvidenceAttachment) for item in attachments):
            raise DetectorEvidenceError(
                "attachments must contain EvidenceAttachment values"
            )
        object.__setattr__(self, "attachments", tuple(attachments))
        object.__setattr__(
            self,
            "disclosure_reference",
            _optional_text(
                self.disclosure_reference,
                field_name="disclosure_reference",
            ),
        )
        object.__setattr__(
            self,
            "source_label",
            _optional_text(self.source_label, field_name="source_label"),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": EVIDENCE_SCHEMA,
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "source_sha256": self.source_sha256,
            "evidence_audio_sha256": self.evidence_audio_sha256,
            "ground_truth_origin": self.ground_truth_origin,
            "ground_truth_basis": self.ground_truth_basis,
            "ground_truth_confidence": self.ground_truth_confidence,
            "created_at_utc": self.created_at_utc,
            "processing_history": [item.to_dict() for item in self.processing_history],
            "detector_results": [item.to_dict() for item in self.detector_results],
            "environment": _json_object(self.environment, field_name="environment"),
            "reproduction_count": self.reproduction_count,
            "reproduction_status": self.reproduction_status,
            "attachments": [item.to_dict() for item in self.attachments],
        }
        if self.disclosure_reference is not None:
            payload["disclosure_reference"] = self.disclosure_reference
        if self.source_label is not None:
            payload["source_label"] = self.source_label
        return payload

    def canonical_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )

    @property
    def evidence_id(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, payload: Any) -> DetectorEvidenceSample:
        record = _record(payload, field_name="evidence sample")
        if record.get("schema") != EVIDENCE_SCHEMA:
            raise DetectorEvidenceError(f"schema must be {EVIDENCE_SCHEMA!r}")
        if record.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
            raise DetectorEvidenceError(
                f"schema_version must be {EVIDENCE_SCHEMA_VERSION}"
            )

        history_raw = _array(
            record.get("processing_history", []),
            field_name="processing_history",
        )
        results_raw = _array(
            record.get("detector_results", []),
            field_name="detector_results",
        )
        attachments_raw = _array(
            record.get("attachments", []),
            field_name="attachments",
        )
        return cls(
            source_sha256=record.get("source_sha256"),
            evidence_audio_sha256=record.get("evidence_audio_sha256"),
            ground_truth_origin=record.get("ground_truth_origin"),
            ground_truth_basis=record.get("ground_truth_basis"),
            ground_truth_confidence=record.get("ground_truth_confidence"),
            created_at_utc=record.get("created_at_utc"),
            processing_history=tuple(
                ProcessingStep.from_dict(item) for item in history_raw
            ),
            detector_results=tuple(
                DetectorResult.from_dict(item) for item in results_raw
            ),
            environment=record.get("environment", {}),
            reproduction_count=record.get("reproduction_count", 1),
            reproduction_status=record.get("reproduction_status", "single"),
            attachments=tuple(
                EvidenceAttachment.from_dict(item) for item in attachments_raw
            ),
            disclosure_reference=record.get("disclosure_reference"),
            source_label=record.get("source_label"),
        )
