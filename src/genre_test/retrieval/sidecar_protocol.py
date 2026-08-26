from __future__ import annotations

import base64
import json
import struct
from dataclasses import dataclass
from typing import Any

PROTOCOL_VERSION = "1"


class SidecarProtocolError(RuntimeError):
    pass


def _decode_json_object(raw: str, *, kind: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SidecarProtocolError(f"sidecar {kind} is invalid JSON") from exc
    if not isinstance(data, dict):
        raise SidecarProtocolError(f"sidecar {kind} must be a JSON object")
    if data.get("protocol") != PROTOCOL_VERSION:
        raise SidecarProtocolError(
            f"unsupported sidecar protocol {data.get('protocol')!r}"
        )
    return data


@dataclass(frozen=True)
class SidecarRequest:
    op: str
    request_id: str
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.op.strip():
            raise SidecarProtocolError("sidecar request missing op")
        if not self.request_id.strip():
            raise SidecarProtocolError("sidecar request missing request_id")

    def to_json(self) -> str:
        return json.dumps(
            {
                "protocol": PROTOCOL_VERSION,
                "op": self.op,
                "request_id": self.request_id,
                "payload": self.payload,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def from_json(cls, raw: str) -> SidecarRequest:
        data = _decode_json_object(raw, kind="request")
        op = str(data.get("op", "")).strip()
        request_id = str(data.get("request_id", "")).strip()
        payload = data.get("payload")
        if not isinstance(payload, dict):
            payload = {}
        return cls(op=op, request_id=request_id, payload=payload)


@dataclass(frozen=True)
class SidecarResponse:
    request_id: str
    ok: bool
    payload: dict[str, Any]
    error_code: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise SidecarProtocolError("sidecar response missing request_id")
        if self.ok and (self.error_code is not None or self.error_message is not None):
            raise SidecarProtocolError("successful sidecar response cannot contain an error")

    def to_json(self) -> str:
        return json.dumps(
            {
                "protocol": PROTOCOL_VERSION,
                "request_id": self.request_id,
                "ok": self.ok,
                "payload": self.payload,
                "error_code": self.error_code,
                "error_message": self.error_message,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def from_json(cls, raw: str) -> SidecarResponse:
        data = _decode_json_object(raw, kind="response")
        request_id = str(data.get("request_id", "")).strip()
        ok = data.get("ok")
        if not isinstance(ok, bool):
            raise SidecarProtocolError("sidecar response field 'ok' must be boolean")
        payload = data.get("payload")
        if not isinstance(payload, dict):
            payload = {}
        return cls(
            request_id=request_id,
            ok=ok,
            payload=payload,
            error_code=data.get("error_code"),
            error_message=data.get("error_message"),
        )


def encode_vector_f32(values: tuple[float, ...]) -> dict[str, Any]:
    blob = struct.pack(f"<{len(values)}f", *values)
    return {
        "encoding": "f32le-base64",
        "dimension": len(values),
        "data": base64.b64encode(blob).decode("ascii"),
    }


def decode_vector_f32(payload: dict[str, Any]) -> tuple[float, ...]:
    if payload.get("encoding") != "f32le-base64":
        raise SidecarProtocolError("unsupported vector encoding")
    try:
        dimension = int(payload["dimension"])
        blob = base64.b64decode(payload["data"], validate=True)
    except (KeyError, TypeError, ValueError) as exc:
        raise SidecarProtocolError("invalid encoded vector payload") from exc
    if dimension <= 0 or len(blob) != dimension * 4:
        raise SidecarProtocolError("vector payload dimension/size mismatch")
    return tuple(struct.unpack(f"<{dimension}f", blob))
