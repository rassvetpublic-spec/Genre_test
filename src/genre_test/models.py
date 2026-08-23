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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AudioFeatures":
        return cls(
            duration_s=float(data.get("duration_s", 0.0)),
            sample_rate=int(data.get("sample_rate", 16000)),
            bpm=float(data["bpm"]) if data.get("bpm") is not None else None,
            key=str(data["key"]) if data.get("key") is not None else None,
            mode=str(data["mode"]) if data.get("mode") is not None else None,
            rms=float(data.get("rms", 0.0)),
            spectral_centroid_hz=float(data.get("spectral_centroid_hz", 0.0)),
            spectral_rolloff_hz=float(data.get("spectral_rolloff_hz", 0.0)),
            zero_crossing_rate=float(data.get("zero_crossing_rate", 0.0)),
        )


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
    schema_version: int = 1
    analyzer_version: str = "legacy-unknown"
    run_id: str | None = None
    analyzed_at: str | None = None
    track_id: str | None = None
    window_seconds: float = 30.0
    internal_top_k: int = 25
    report_top_k: int = 15
    git_commit: str | None = None
    source_file_size: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnalysisResult":
        top_styles = [
            item
            if isinstance(item, StyleScore)
            else StyleScore(str(item["label"]), float(item["score"]))
            for item in data.get("top_styles", [])
        ]
        broad_genres = [
            item
            if isinstance(item, StyleScore)
            else StyleScore(str(item["label"]), float(item["score"]))
            for item in data.get("broad_genres", [])
        ]
        audio_data = data.get("audio_features") or {}
        audio_features = (
            audio_data
            if isinstance(audio_data, AudioFeatures)
            else AudioFeatures.from_dict(audio_data)
        )
        return cls(
            path=str(data.get("path", "")),
            primary_genre=data.get("primary_genre"),
            primary_genre_score=(
                float(data["primary_genre_score"])
                if data.get("primary_genre_score") is not None
                else None
            ),
            top_styles=top_styles,
            broad_genres=broad_genres,
            audio_features=audio_features,
            model_id=str(data.get("model_id", "unknown")),
            model_revision=data.get("model_revision"),
            windows_analyzed=int(data.get("windows_analyzed", 0)),
            device=str(data.get("device", "unknown")),
            resolved_genre=data.get("resolved_genre"),
            classification=str(data.get("classification", "unknown")),
            confidence=str(data.get("confidence", "low")),
            family_margin=(
                float(data["family_margin"]) if data.get("family_margin") is not None else None
            ),
            secondary_genre=data.get("secondary_genre"),
            family_ratio=(
                float(data["family_ratio"]) if data.get("family_ratio") is not None else None
            ),
            style_margin=(
                float(data["style_margin"]) if data.get("style_margin") is not None else None
            ),
            secondary_style=data.get("secondary_style"),
            analysis_mode=str(data.get("analysis_mode", "expert")),
            schema_version=int(data.get("schema_version", 1)),
            analyzer_version=str(data.get("analyzer_version", "legacy-unknown")),
            run_id=data.get("run_id"),
            analyzed_at=data.get("analyzed_at"),
            track_id=data.get("track_id"),
            window_seconds=float(data.get("window_seconds", 30.0)),
            internal_top_k=int(data.get("internal_top_k", 25)),
            report_top_k=int(data.get("report_top_k", len(top_styles) or 15)),
            git_commit=data.get("git_commit"),
            source_file_size=(
                int(data["source_file_size"])
                if data.get("source_file_size") is not None
                else None
            ),
        )

    @property
    def stem(self) -> str:
        return Path(self.path).stem
