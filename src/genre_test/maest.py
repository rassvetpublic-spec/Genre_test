from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from transformers import pipeline

DEFAULT_MODEL = "mtg-upf/discogs-maest-30s-pw-129e-519l"


@dataclass
class MaestClassifier:
    model_id: str = DEFAULT_MODEL
    revision: str | None = None
    device: str = "auto"

    def __post_init__(self) -> None:
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

    def predict(self, audio_16k: np.ndarray, top_k: int = 25) -> list[dict[str, float | str]]:
        result = self._pipe(audio_16k, top_k=top_k)
        return [{"label": str(x["label"]), "score": float(x["score"])} for x in result]
