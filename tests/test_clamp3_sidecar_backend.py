from __future__ import annotations

import sys
from pathlib import Path

import pytest

from genre_test.retrieval.clamp3_sidecar_backend import (
    Clamp3SidecarBackend,
    Clamp3SidecarError,
)
from genre_test.retrieval.contracts import RetrievalBackendInfo
from genre_test.retrieval.sidecar_protocol import SidecarRequest, SidecarResponse


_FAKE_SIDECAR = r'''
import base64
import json
import struct
import sys

PROTOCOL = "1"


def vector(values):
    blob = struct.pack(f"<{len(values)}f", *values)
    return {
        "encoding": "f32le-base64",
        "dimension": len(values),
        "data": base64.b64encode(blob).decode("ascii"),
    }


def response(request_id, ok, payload=None, error_code=None, error_message=None):
    return json.dumps(
        {
            "protocol": PROTOCOL,
            "request_id": request_id,
            "ok": ok,
            "payload": payload or {},
            "error_code": error_code,
            "error_message": error_message,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


for raw in sys.stdin:
    request = json.loads(raw)
    request_id = request["request_id"]
    op = request["op"]
    payload = request.get("payload") or {}
    if op == "health":
        print(
            response(
                request_id,
                True,
                {
                    "status": "OK",
                    "value": "fake sidecar ready",
                    "details": "test runtime",
                },
            ),
            flush=True,
        )
    elif op == "embed_text":
        if payload.get("text") == "fail":
            print(
                response(
                    request_id,
                    False,
                    error_code="TEST_FAILURE",
                    error_message="forced failure",
                ),
                flush=True,
            )
        else:
            print(response(request_id, True, {"vector": vector([0.0, 1.0, 0.0])}), flush=True)
    elif op == "embed_audio":
        print(response(request_id, True, {"vector": vector([1.0, 0.0, 0.0])}), flush=True)
    elif op == "shutdown":
        print(response(request_id, True, {"shutdown": True}), flush=True)
        break
    else:
        print(
            response(request_id, False, error_code="UNKNOWN_OP", error_message=op),
            flush=True,
        )
'''


def _test_info() -> RetrievalBackendInfo:
    return RetrievalBackendInfo(
        backend_name="fake-clamp-sidecar",
        backend_version="test",
        clamp_code_revision="test-code",
        clamp_weight_name="test.pth",
        clamp_weight_sha256="a" * 64,
        mert_model_id="test-mert",
        mert_revision="test-mert-rev",
        text_model_id="test-text",
        text_model_revision="test-text-rev",
        text_tokenizer_revision="test-text-rev",
        preprocessing_version="test-preprocess",
        embedding_dim=3,
    )


def _backend(tmp_path: Path) -> Clamp3SidecarBackend:
    script = tmp_path / "fake_sidecar.py"
    script.write_text(_FAKE_SIDECAR, encoding="utf-8")
    return Clamp3SidecarBackend(
        python_executable=Path(sys.executable),
        script_path=script,
        runtime_root=tmp_path,
        upstream_root=tmp_path,
        request_timeout_s=5.0,
        info=_test_info(),
    )


def test_sidecar_protocol_request_and_response_roundtrip_unicode() -> None:
    request = SidecarRequest(
        op="embed_text",
        request_id="abc",
        payload={"text": "мрачный трек", "language": "ru"},
    )
    assert SidecarRequest.from_json(request.to_json()) == request

    response = SidecarResponse(
        request_id="abc",
        ok=True,
        payload={"status": "OK"},
    )
    assert SidecarResponse.from_json(response.to_json()) == response


def test_sidecar_backend_health_text_audio_and_shutdown(tmp_path: Path) -> None:
    audio = tmp_path / "track.wav"
    audio.write_bytes(b"fixture")

    backend = _backend(tmp_path)
    try:
        health = backend.health()
        assert health.status == "OK"
        assert health.value == "fake sidecar ready"
        assert backend.is_running

        text = backend.embed_text("русский запрос", language="RU")
        assert text.values == pytest.approx((0.0, 1.0, 0.0))
        assert text.identity.scope == "text"
        assert text.identity.language == "ru"

        audio_vector = backend.embed_audio(audio, track_id="track-1")
        assert audio_vector.values == pytest.approx((1.0, 0.0, 0.0))
        assert audio_vector.identity.scope == "full"
    finally:
        backend.close()

    assert not backend.is_running


def test_sidecar_backend_preserves_segment_identity(tmp_path: Path) -> None:
    audio = tmp_path / "track.wav"
    audio.write_bytes(b"fixture")

    with _backend(tmp_path) as backend:
        vector = backend.embed_audio(
            audio,
            track_id="track-1",
            start_s=10.0,
            end_s=20.0,
        )

    assert vector.identity.scope == "segment"
    assert vector.identity.start_s == 10.0
    assert vector.identity.end_s == 20.0


def test_sidecar_backend_propagates_structured_error(tmp_path: Path) -> None:
    with _backend(tmp_path) as backend:
        with pytest.raises(Clamp3SidecarError) as raised:
            backend.embed_text("fail", language="en")

    assert raised.value.code == "TEST_FAILURE"
    assert raised.value.message == "forced failure"


def test_sidecar_backend_missing_runtime_is_na(tmp_path: Path) -> None:
    backend = Clamp3SidecarBackend(
        python_executable=tmp_path / "missing-python.exe",
        script_path=tmp_path / "missing-sidecar.py",
        runtime_root=tmp_path,
        info=_test_info(),
    )

    health = backend.health()
    assert health.status == "N/A"
    assert "not installed" in health.value.lower()


def test_sidecar_backend_rejects_partial_segment_bounds(tmp_path: Path) -> None:
    audio = tmp_path / "track.wav"
    audio.write_bytes(b"fixture")

    backend = _backend(tmp_path)
    with pytest.raises(ValueError, match="supplied together"):
        backend.embed_audio(audio, track_id="track-1", start_s=10.0)
