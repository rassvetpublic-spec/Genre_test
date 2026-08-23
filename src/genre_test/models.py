from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StyleScore:
    label: str
    score: float


@dataclass(frozen=True)
class AudioFeatures:
    duration_s: float
    sample_rate: int
    bpm: float | None
    key: str | None
    mode: str | None
    rms: float
    spectral_centroid_hz: float
    spectral_rolloff_hz: float
    zero_crossing_rate: float


@dataclass(frozen=True)
class AnalysisResult:
    path: str
    primary_genre: str | None
    primary_genre_score: float | None
    top_styles: list[StyleScore]
    broad_genres: list[StyleScore]
    audio_features: AudioFeatures
    model_id: str
    model_revision: str | None
    windows_analyzed: int
    device: str
    resolved_genre: str | None = None
    classification: str = "unknown"
    confidence: str = "low"
    family_margin: float | None = None
    secondary_genre: str | None = None
    family_ratio: float | None = None
    style_margin: float | None = None
    secondary_style: str | None = None
    analysis_mode: str = "expert"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def stem(self) -> str:
        return Path(self.path).stem
