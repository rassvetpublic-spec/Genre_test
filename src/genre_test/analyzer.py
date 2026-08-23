from __future__ import annotations

from pathlib import Path

from .aggregate import aggregate_predictions
from .audio import load_audio, select_windows
from .features import extract_audio_features
from .maest import DEFAULT_MODEL, MaestClassifier
from .models import AnalysisResult
from .resolver import resolve_genre


class GenreAnalyzer:
    def __init__(
        self,
        model_id: str = DEFAULT_MODEL,
        revision: str | None = None,
        device: str = "auto",
        sample_rate: int = 16000,
        window_seconds: float = 30.0,
        window_count: int = 5,
        top_k: int = 15,
    ) -> None:
        self.sample_rate = sample_rate
        self.window_seconds = window_seconds
        self.window_count = window_count
        self.top_k = top_k
        self.classifier = MaestClassifier(model_id=model_id, revision=revision, device=device)

    def analyze(self, path: Path) -> AnalysisResult:
        audio, sr = load_audio(path, self.sample_rate)
        features = extract_audio_features(audio, sr)
        windows = select_windows(audio, sr, self.window_seconds, self.window_count)
        predictions = [self.classifier.predict(w, top_k=max(25, self.top_k)) for w in windows]
        styles, genres = aggregate_predictions(predictions, top_k=self.top_k)
        primary = genres[0] if genres else None
        resolution = resolve_genre(styles, genres)
        return AnalysisResult(
            path=str(path.resolve()),
            primary_genre=primary.label if primary else None,
            primary_genre_score=round(primary.score, 6) if primary else None,
            resolved_genre=resolution.resolved_genre,
            classification=resolution.classification,
            confidence=resolution.confidence,
            family_margin=resolution.family_margin,
            secondary_genre=resolution.secondary_family,
            family_ratio=resolution.family_ratio,
            style_margin=resolution.style_margin,
            secondary_style=resolution.secondary_style,
            top_styles=styles,
            broad_genres=genres,
            audio_features=features,
            model_id=self.classifier.model_id,
            model_revision=self.classifier.revision,
            windows_analyzed=len(windows),
            device=self.classifier.resolved_device,
        )
