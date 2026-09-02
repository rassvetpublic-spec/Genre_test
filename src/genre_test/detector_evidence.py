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

_PROCESSING_KEYS = frozenset({"operation", "tool_id", "tool_version", "parameters", "note"})
_DETECTOR_KEYS = frozenset(
    {
        "detector_id",
        "detector_version",
        "tested_at_utc",
        "verdict",
        "verdict_semantics",
        "raw_response",
        "score",
        "confidence",
        "service_id",
        "service_version",
        "model_id",
        "model_revision",
    }
)
_ATTACHMENT_KEYS = frozenset({"kind", "sha256", "media_type", "label"})
_SAMPLE_KEYS = frozenset(
    {
        "schema",
        "schema_version",
        "source_sha256",
        "evidence_audio_sha256",
        "transformation_class",
        "ground_truth_origin",
        "ground_truth_basis",
        "ground_truth_confidence",
        "created_at_utc",
        "processing_history",
        "detector_results",
        "environment",
        "reproduction_count",
        "reproduction_status",
        "attachments",
        "disclosure_reference",
        "source_label",
    }
)


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


def _reject_unknown_keys(
    record: Mapping[str, Any],
    *,
    allowed: frozenset[str],
    field_name: str,
) -> None:
    unknown = sorted(set(record) - allowed)
    if unknown:
        raise DetectorEvidenceError(
            f"{field_name} contains unknown fields: {', '.join(unknown)}"
        )


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


def _bounded_json_object(
    value: Any,
    *,
    field_name: str,
    max_bytes: int = 8192,
) -> dict[str, Any]:
    normalized = _json_object(value, field_name=field_name)
    if not normalized:
        raise DetectorEvidenceError(f"{field_name} must be a non-empty JSON object")
    encoded = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if len(encoded) > max_bytes:
        raise DetectorEvidenceError(f"{field_name} exceeds {max_bytes} UTF-8 bytes")
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
        _reject_unknown_keys(
            record,
            allowed=_PROCESSING_KEYS,
            field_name="processing_history item",
        )
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
    verdict_semantics: Mapping[str, Any]
    raw_response: Mapping[str, Any]
    score: float | None = None
    confidence: float | None = None
    service_id: str | None = None
    service_version: str | None = None
    model_id: str | None = None
    model_revision: str | None = None

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
            "verdict_semantics",
            _bounded_json_object(
                self.verdict_semantics,
                field_name="detector.verdict_semantics",
            ),
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

        service_id = _optional_text(self.service_id, field_name="detector.service_id")
        service_version = _optional_text(
            self.service_version,
            field_name="detector.service_version",
        )
        model_id = _optional_text(self.model_id, field_name="detector.model_id")
        model_revision = _optional_text(
            self.model_revision,
            field_name="detector.model_revision",
        )
        if service_version is not None and service_id is None:
            raise DetectorEvidenceError("detector.service_version requires service_id")
        if model_revision is not None and model_id is None:
            raise DetectorEvidenceError("detector.model_revision requires model_id")
        object.__setattr__(self, "service_id", service_id)
        object.__setattr__(self, "service_version", service_version)
        object.__setattr__(self, "model_id", model_id)
        object.__setattr__(self, "model_revision", model_revision)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "detector_id": self.detector_id,
            "detector_version": self.detector_version,
            "tested_at_utc": self.tested_at_utc,
            "verdict": self.verdict,
            "verdict_semantics": _bounded_json_object(
                self.verdict_semantics,
                field_name="detector.verdict_semantics",
            ),
            "raw_response": _json_object(
                self.raw_response,
                field_name="detector.raw_response",
            ),
        }
        if self.score is not None:
            payload["score"] = self.score
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        if self.service_id is not None:
            payload["service_id"] = self.service_id
        if self.service_version is not None:
            payload["service_version"] = self.service_version
        if self.model_id is not None:
            payload["model_id"] = self.model_id
        if self.model_revision is not None:
            payload["model_revision"] = self.model_revision
        return payload

    @classmethod
    def from_dict(cls, payload: Any) -> DetectorResult:
        record = _record(payload, field_name="detector_results item")
        _reject_unknown_keys(
            record,
            allowed=_DETECTOR_KEYS,
            field_name="detector_results item",
        )
        return cls(
            detector_id=record.get("detector_id"),
            detector_version=record.get("detector_version"),
            tested_at_utc=record.get("tested_at_utc"),
            verdict=record.get("verdict"),
            verdict_semantics=record.get("verdict_semantics", {}),
            raw_response=record.get("raw_response", {}),
            score=record.get("score"),
            confidence=record.get("confidence"),
            service_id=record.get("service_id"),
            service_version=record.get("service_version"),
            model_id=record.get("model_id"),
            model_revision=record.get("model_revision"),
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
        _reject_unknown_keys(
            record,
            allowed=_ATTACHMENT_KEYS,
            field_name="attachments item",
        )
        return cls(
            kind=record.get("kind"),
            sha256=record.get("sha256"),
            media_type=record.get("media_type"),
            label=record.get("label"),
        )


@dataclass(frozen=True)
class DetectorEvidenceSample:
    """Versioned evidence that binds ground truth, transformation class, lineage, and detector outputs."""

    source_sha256: str
    evidence_audio_sha256: str
    transformation_class: str
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
            "transformation_class",
            _required_text(self.transformation_class, field_name="transformation_class"),
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
        history_tuple = tuple(history)
        if self.source_sha256 != self.evidence_audio_sha256 and not history_tuple:
            raise DetectorEvidenceError(
                "changed evidence audio requires at least one processing_history step"
            )
        object.__setattr__(self, "processing_history", history_tuple)

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
            "transformation_class": self.transformation_class,
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
        _reject_unknown_keys(record, allowed=_SAMPLE_KEYS, field_name="evidence sample")
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
            transformation_class=record.get("transformation_class"),
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
