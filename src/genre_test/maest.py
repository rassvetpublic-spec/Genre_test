from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Iterable

from .runtime_meta import default_hf_home

# Keep model/cache data inside the project checkout unless the user explicitly overrides HF_HOME.
_hf_home = default_hf_home()
_hf_home.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("HF_HOME", str(_hf_home))

import numpy as np
import torch
from transformers import pipeline

DEFAULT_MODEL = "mtg-upf/discogs-maest-30s-pw-129e-519l"
DEFAULT_MODEL_REVISION = "6c35f32a350f74351870937d5ae0bae1d898d1df"
DEFAULT_CUDA_BATCH_SIZE = 8

Prediction = list[dict[str, float | str]]


@dataclass
class MaestClassifier:
    model_id: str = DEFAULT_MODEL
    revision: str | None = None
    device: str = "auto"
    last_batch_size: int = field(init=False, default=1)

    def __post_init__(self) -> None:
        if self.revision is None and self.model_id == DEFAULT_MODEL:
            self.revision = DEFAULT_MODEL_REVISION

        resolved = self._resolve_device(self.device)
        device_arg: int | str = 0 if resolved == "cuda" else "cpu"
        kwargs: dict[str, object] = {
            "task": "audio-classification",
            "model": self.model_id,
            "device": device_arg,
            "trust_remote_code": True,
        }
        if self.revision:
            kwargs["revision"] = self.revision
        self._pipe = pipeline(**kwargs)
        self.resolved_device = resolved

    @staticmethod
    def _resolve_device(device: str) -> str:
        normalized = device.lower().strip()
        if normalized == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        if normalized == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but torch.cuda.is_available() is False")
        if normalized not in {"cpu", "cuda"}:
            raise ValueError("device must be auto, cpu or cuda")
        return normalized

    def default_batch_size(self, item_count: int) -> int:
        if item_count <= 0:
            return 1
        if self.resolved_device == "cuda":
            return min(DEFAULT_CUDA_BATCH_SIZE, item_count)
        return 1

    @staticmethod
    def _normalize_prediction(result: Iterable[dict[str, object]]) -> Prediction:
        return [
            {"label": str(item["label"]), "score": float(item["score"])}
            for item in result
        ]

    def predict(self, audio_16k: np.ndarray, top_k: int = 25) -> Prediction:
        self.last_batch_size = 1
        result = self._pipe(audio_16k, top_k=top_k)
        return self._normalize_prediction(result)

    def predict_batch(
        self,
        audio_windows: Iterable[np.ndarray],
        top_k: int = 25,
        batch_size: int | None = None,
    ) -> list[Prediction]:
        windows = list(audio_windows)
        if not windows:
            return []
        if len(windows) == 1:
            return [self.predict(windows[0], top_k=top_k)]

        effective_batch_size = batch_size or self.default_batch_size(len(windows))
        effective_batch_size = max(1, min(effective_batch_size, len(windows)))
        self.last_batch_size = effective_batch_size
        try:
            result = self._pipe(
                windows,
                top_k=top_k,
                batch_size=effective_batch_size,
            )
        except RuntimeError as exc:
            # A long 30 s audio batch can exceed VRAM on smaller GPUs. Retry with progressively
            # smaller batches rather than failing the whole analysis session.
            if self.resolved_device != "cuda" or "out of memory" not in str(exc).lower():
                raise
            torch.cuda.empty_cache()
            if effective_batch_size <= 1:
                raise
            return self.predict_batch(
                windows,
                top_k=top_k,
                batch_size=max(1, effective_batch_size // 2),
            )

        return [self._normalize_prediction(items) for items in result]
