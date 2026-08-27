from __future__ import annotations

import argparse
import gc
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


REPO_ROOT = _repo_root()
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from clamp3_runtime_smoke import (  # noqa: E402
    _audio_embedding,
    _existing_assets,
    _load_clamp,
    _load_mert_extractor,
    _runtime_versions,
    _text_embedding,
    _waveform_from_audio_array,
)
from genre_test.retrieval.model_pins import (  # noqa: E402
    CLAMP3_WEIGHT_FILENAME,
    EMBEDDING_DIMENSION,
    MIN_FINAL_WINDOW_SECONDS,
    TARGET_SAMPLE_RATE,
    WINDOW_SECONDS,
    manifest_fingerprint,
    verify_clamp3_weight,
)
from genre_test.retrieval.sidecar_protocol import (  # noqa: E402
    SidecarProtocolError,
    SidecarRequest,
    SidecarResponse,
    encode_vector_f32,
)


class Clamp3RuntimeEngine:
    def __init__(self, *, runtime_root: Path, upstream_root: Path) -> None:
        self.runtime_root = runtime_root
        self.upstream_root = upstream_root
        self.assets: dict[str, Path] | None = None
        self.model: Any = None
        self.tokenizer: Any = None
        self.device: Any = None
        self.checkpoint: dict[str, Any] | None = None
        self.mert_extractor: Any = None

    def _presence(self) -> tuple[bool, list[str]]:
        missing: list[str] = []
        models_root = self.runtime_root / "models"
        clamp_weight = models_root / "clamp3-saas" / CLAMP3_WEIGHT_FILENAME
        if not verify_clamp3_weight(clamp_weight):
            missing.append("pinned CLaMP SAAS weight (missing/corrupt)")
        if not (models_root / "mert-v1-95m" / "config.json").is_file():
            missing.append("MERT snapshot")
        if not (models_root / "xlm-roberta-base" / "config.json").is_file():
            missing.append("XLM-R snapshot")
        if not (self.upstream_root / "code").is_dir():
            missing.append("pinned CLaMP source checkout")
        return not missing, missing

    def health_payload(self) -> dict[str, Any]:
        ready, missing = self._presence()
        loaded = self.model is not None
        if ready:
            status = "OK"
            value = "CLaMP 3 sidecar ready"
            details = "Pinned runtime assets are present and CLaMP weight checksum is valid."
        else:
            status = "WARN"
            value = "CLaMP 3 sidecar installed; models/source incomplete"
            details = "Missing: " + ", ".join(missing)
        return {
            "status": status,
            "value": value,
            "details": details,
            "loaded": loaded,
            "manifest_fingerprint": manifest_fingerprint(),
            "runtime_versions": _runtime_versions(),
            "device": str(self.device) if self.device is not None else None,
        }

    def _ensure_clamp(self) -> None:
        if self.model is not None:
            return
        self.assets = _existing_assets(self.runtime_root)
        model, tokenizer, device, checkpoint = _load_clamp(
            self.upstream_root,
            self.assets,
        )
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.checkpoint = checkpoint

    def _ensure_mert(self) -> None:
        self._ensure_clamp()
        if self.mert_extractor is not None:
            return
        assert self.assets is not None
        self.mert_extractor = _load_mert_extractor(
            self.upstream_root,
            self.assets["mert_dir"],
            self.device,
        )

    def embed_text(self, text: str) -> tuple[float, ...]:
        if not text.strip():
            raise ValueError("text query must not be empty")
        self._ensure_clamp()
        vector = _text_embedding(
            self.model,
            self.tokenizer,
            text.strip(),
            self.device,
        ).detach().cpu()
        return tuple(float(value) for value in vector.tolist())

    def _load_audio_segment(
        self,
        path: Path,
        *,
        start_s: float | None,
        end_s: float | None,
    ):
        import soundfile as sf

        with sf.SoundFile(str(path)) as handle:
            sample_rate = int(handle.samplerate)
            total_frames = int(len(handle))
            if start_s is None and end_s is None:
                start_frame = 0
                end_frame = total_frames
            else:
                if start_s is None or end_s is None:
                    raise ValueError("start_s and end_s must be supplied together")
                if start_s < 0 or end_s <= start_s:
                    raise ValueError("segment bounds must satisfy 0 <= start_s < end_s")
                start_frame = int(round(start_s * sample_rate))
                end_frame = int(round(end_s * sample_rate))
                if start_frame >= total_frames:
                    raise ValueError("segment starts after end of audio")
                end_frame = min(end_frame, total_frames)
                if end_frame <= start_frame:
                    raise ValueError("segment contains no samples")
            handle.seek(start_frame)
            data = handle.read(
                frames=end_frame - start_frame,
                dtype="float32",
                always_2d=True,
            )

        return _waveform_from_audio_array(data, sample_rate, self.device)

    def _mert_features_for_audio(
        self,
        path: Path,
        *,
        start_s: float | None,
        end_s: float | None,
    ):
        import torch

        self._ensure_mert()
        waveform = self._load_audio_segment(path, start_s=start_s, end_s=end_s)
        processed = self.mert_extractor.process_wav(waveform).to(self.device)
        if processed.ndim == 1:
            processed = processed.unsqueeze(0)
        if processed.ndim != 2:
            raise ValueError(
                f"unexpected processed waveform shape: {tuple(processed.shape)}"
            )

        window_samples = int(TARGET_SAMPLE_RATE * WINDOW_SECONDS)
        min_final_samples = int(TARGET_SAMPLE_RATE * MIN_FINAL_WINDOW_SECONDS)
        chunks = [
            processed[:, start : start + window_samples]
            for start in range(0, processed.shape[-1], window_samples)
        ]
        if chunks and chunks[-1].shape[-1] < min_final_samples:
            chunks = chunks[:-1]
        if not chunks:
            raise ValueError("audio is too short for CLaMP/MERT preprocessing")

        features: list[Any] = []
        with torch.no_grad():
            for chunk in chunks:
                features.append(
                    self.mert_extractor(chunk, layer=None, reduction="mean")
                )
        merged = torch.cat(features, dim=1)
        return merged.mean(dim=0, keepdim=True).reshape(-1, EMBEDDING_DIMENSION)

    def embed_audio(
        self,
        path: Path,
        *,
        start_s: float | None,
        end_s: float | None,
    ) -> tuple[float, ...]:
        if not path.is_file():
            raise FileNotFoundError(path)
        features = self._mert_features_for_audio(
            path,
            start_s=start_s,
            end_s=end_s,
        )
        vector = _audio_embedding(self.model, features, self.device).detach().cpu()
        return tuple(float(value) for value in vector.tolist())

    def close(self) -> None:
        self.mert_extractor = None
        self.model = None
        self.tokenizer = None
        self.checkpoint = None
        self.assets = None
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass


def _error_response(request_id: str, code: str, message: str) -> SidecarResponse:
    return SidecarResponse(
        request_id=request_id,
        ok=False,
        payload={},
        error_code=code,
        error_message=message,
    )


def _handle(engine: Clamp3RuntimeEngine, request: SidecarRequest) -> tuple[SidecarResponse, bool]:
    try:
        if request.op == "health":
            return (
                SidecarResponse(
                    request_id=request.request_id,
                    ok=True,
                    payload=engine.health_payload(),
                ),
                True,
            )
        if request.op == "embed_text":
            text = str(request.payload.get("text", ""))
            vector = engine.embed_text(text)
            return (
                SidecarResponse(
                    request_id=request.request_id,
                    ok=True,
                    payload={"vector": encode_vector_f32(vector)},
                ),
                True,
            )
        if request.op == "embed_audio":
            path = Path(str(request.payload.get("path", "")))
            start_raw = request.payload.get("start_s")
            end_raw = request.payload.get("end_s")
            start_s = float(start_raw) if start_raw is not None else None
            end_s = float(end_raw) if end_raw is not None else None
            vector = engine.embed_audio(path, start_s=start_s, end_s=end_s)
            return (
                SidecarResponse(
                    request_id=request.request_id,
                    ok=True,
                    payload={"vector": encode_vector_f32(vector)},
                ),
                True,
            )
        if request.op == "shutdown":
            engine.close()
            return (
                SidecarResponse(
                    request_id=request.request_id,
                    ok=True,
                    payload={"shutdown": True},
                ),
                False,
            )
        return _error_response(request.request_id, "UNKNOWN_OP", request.op), True
    except FileNotFoundError as exc:
        return _error_response(request.request_id, "MODEL_OR_FILE_MISSING", str(exc)), True
    except ValueError as exc:
        return _error_response(request.request_id, "INVALID_REQUEST", str(exc)), True
    except Exception as exc:  # pragma: no cover - real model/runtime boundary
        message = str(exc)
        code = "CUDA_OOM" if "out of memory" in message.lower() else "INFERENCE_FAILED"
        return _error_response(request.request_id, code, message), True


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Persistent Genre_test CLaMP 3 sidecar")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--upstream-root", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    engine = Clamp3RuntimeEngine(
        runtime_root=args.runtime_root.resolve(),
        upstream_root=args.upstream_root.resolve(),
    )
    keep_running = True
    while keep_running:
        raw = sys.stdin.readline()
        if raw == "":
            break
        if not raw.strip():
            continue
        try:
            request = SidecarRequest.from_json(raw)
            # Third-party model code may print progress/status lines. Keep protocol stdout
            # reserved exclusively for one JSON response per request.
            with redirect_stdout(sys.stderr):
                response, keep_running = _handle(engine, request)
        except SidecarProtocolError as exc:
            response = SidecarResponse(
                request_id="protocol-error",
                ok=False,
                payload={},
                error_code="PROTOCOL_ERROR",
                error_message=str(exc),
            )
        sys.stdout.write(response.to_json() + "\n")
        sys.stdout.flush()
    with redirect_stdout(sys.stderr):
        engine.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
