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
    def from_dict(cls, data: dict[str, Any]) -> AudioFeatures:
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
class SemanticEvidence:
    model_id: str
    model_revision: str | None
    device: str
    windows_analyzed: int
    top_tags: list[StyleScore]
    genre_tags: list[StyleScore]
    mood_tags: list[StyleScore]
    vocal_tags: list[StyleScore]
    instrument_tags: list[StyleScore]
    production_tags: list[StyleScore]
    status: str = "ok"
    notes: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SemanticEvidence:
        def scores(key: str) -> list[StyleScore]:
            return [
                item
                if isinstance(item, StyleScore)
                else StyleScore(str(item["label"]), float(item["score"]))
                for item in data.get(key, [])
            ]

        return cls(
            model_id=str(data.get("model_id", "unknown")),
            model_revision=data.get("model_revision"),
            device=str(data.get("device", "unknown")),
            windows_analyzed=int(data.get("windows_analyzed", 0)),
            top_tags=scores("top_tags"),
            genre_tags=scores("genre_tags"),
            mood_tags=scores("mood_tags"),
            vocal_tags=scores("vocal_tags"),
            instrument_tags=scores("instrument_tags"),
            production_tags=scores("production_tags"),
            status=str(data.get("status", "ok")),
            notes=tuple(str(item) for item in (data.get("notes") or ())),
        )


@dataclass(frozen=True)
class AudioProfile:
    primary_genre: str | None
    broad_family: str | None
    confidence: str
    secondary_influence: str | None
    adjacent_genres: tuple[str, ...]
    moods: tuple[str, ...]
    vocal: str | None
    instruments: tuple[str, ...]
    production: tuple[str, ...]
    distributor_genre: str | None
    distributor_subgenre: str | None
    suno_style: str | None
    ensemble_agreement: str
    ensemble_sources: tuple[str, ...]
    family_evidence: list[StyleScore]
    semantic_status: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AudioProfile:
        evidence = [
            item
            if isinstance(item, StyleScore)
            else StyleScore(str(item["label"]), float(item["score"]))
            for item in data.get("family_evidence", [])
        ]
        return cls(
            primary_genre=data.get("primary_genre"),
            broad_family=data.get("broad_family"),
            confidence=str(data.get("confidence", "low")),
            secondary_influence=data.get("secondary_influence"),
            adjacent_genres=tuple(str(item) for item in data.get("adjacent_genres", [])),
            moods=tuple(str(item) for item in data.get("moods", [])),
            vocal=data.get("vocal"),
            instruments=tuple(str(item) for item in data.get("instruments", [])),
            production=tuple(str(item) for item in data.get("production", [])),
            distributor_genre=data.get("distributor_genre"),
            distributor_subgenre=data.get("distributor_subgenre"),
            suno_style=data.get("suno_style"),
            ensemble_agreement=str(data.get("ensemble_agreement", "maest_only")),
            ensemble_sources=tuple(str(item) for item in data.get("ensemble_sources", [])),
            family_evidence=evidence,
            semantic_status=str(data.get("semantic_status", "not_available")),
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
    input_quality: str = "NORMAL"
    quality_notes: tuple[str, ...] = ()
    semantic_evidence: SemanticEvidence | None = None
    audio_profile: AudioProfile | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnalysisResult:
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
        notes = data.get("quality_notes") or ()
        semantic_data = data.get("semantic_evidence")
        profile_data = data.get("audio_profile")
        semantic_evidence = (
            semantic_data
            if isinstance(semantic_data, SemanticEvidence)
            else SemanticEvidence.from_dict(semantic_data)
            if isinstance(semantic_data, dict)
            else None
        )
        audio_profile = (
            profile_data
            if isinstance(profile_data, AudioProfile)
            else AudioProfile.from_dict(profile_data)
            if isinstance(profile_data, dict)
            else None
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
            input_quality=str(data.get("input_quality", "NORMAL")),
            quality_notes=tuple(str(item) for item in notes),
            semantic_evidence=semantic_evidence,
            audio_profile=audio_profile,
        )

    @property
    def stem(self) -> str:
        return Path(self.path).stem
