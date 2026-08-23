from __future__ import annotations

from pathlib import Path

from .aggregate import aggregate_predictions
from .audio import load_audio, select_windows
from .features import extract_audio_features
from .maest import DEFAULT_MODEL, MaestClassifier
from .models import AnalysisResult, StyleScore
from .resolver import GenreResolution, resolve_genre

ANALYSIS_MODES = {"auto", "fast", "accurate", "expert"}


def duration_window_target(duration_s: float) -> int:
    """Choose the maximum representative-window count from track duration."""
    if duration_s < 60:
        return 1
    if duration_s < 120:
        return 3
    if duration_s < 210:
        return 5
    if duration_s < 300:
        return 7
    if duration_s < 420:
        return 9
    return 11


def spread_indices(total: int, count: int) -> list[int]:
    """Return stable, approximately uniform indices including both ends."""
    if total <= 0 or count <= 0:
        return []
    if count >= total:
        return list(range(total))
    if count == 1:
        return [total // 2]

    indices = [round(i * (total - 1) / (count - 1)) for i in range(count)]
    # Rounding can only duplicate indices for very small grids; keep order if it happens.
    return list(dict.fromkeys(indices))


def needs_more_auto_windows(resolution: GenreResolution) -> bool:
    """Expand Auto analysis when the current genre decision is not stable enough."""
    return resolution.classification == "hybrid" or resolution.confidence != "high"


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
        analysis_mode: str = "auto",
    ) -> None:
        mode = analysis_mode.lower().strip()
        if mode not in ANALYSIS_MODES:
            raise ValueError(f"Unknown analysis mode: {analysis_mode}")
        if window_count < 1:
            raise ValueError("window_count must be >= 1")
        if top_k < 3:
            raise ValueError("top_k must be >= 3")

        self.sample_rate = sample_rate
        self.window_seconds = window_seconds
        self.window_count = window_count
        self.top_k = top_k
        self.analysis_mode = mode
        self.classifier = MaestClassifier(model_id=model_id, revision=revision, device=device)

    def _predict(self, window) -> list[dict[str, float | str]]:
        # Keep more internal candidates than the report needs so the resolver can see competitors.
        return self.classifier.predict(window, top_k=max(25, self.top_k))

    def _resolve_predictions(
        self, predictions: list[list[dict[str, float | str]]]
    ) -> tuple[list[StyleScore], list[StyleScore], GenreResolution]:
        styles, genres = aggregate_predictions(predictions, top_k=self.top_k)
        return styles, genres, resolve_genre(styles, genres)

    def _run_windows(
        self,
        audio,
        sr: int,
        duration_s: float,
    ) -> tuple[list[list[dict[str, float | str]]], int]:
        target = duration_window_target(duration_s)

        if self.analysis_mode == "expert":
            windows = select_windows(audio, sr, self.window_seconds, self.window_count)
            return [self._predict(window) for window in windows], len(windows)

        if self.analysis_mode == "fast":
            windows = select_windows(audio, sr, self.window_seconds, min(target, 3))
            return [self._predict(window) for window in windows], len(windows)

        windows = select_windows(audio, sr, self.window_seconds, target)

        if self.analysis_mode == "accurate" or len(windows) <= 5:
            return [self._predict(window) for window in windows], len(windows)

        # Auto: begin with five windows spread across the same final grid. If those already produce
        # a high-confidence primary decision, stop. Otherwise analyze the remaining grid points.
        initial_indices = spread_indices(len(windows), 5)
        prediction_by_index = {index: self._predict(windows[index]) for index in initial_indices}
        initial_predictions = [prediction_by_index[index] for index in initial_indices]
        _, _, resolution = self._resolve_predictions(initial_predictions)

        if not needs_more_auto_windows(resolution):
            return initial_predictions, len(initial_predictions)

        for index, window in enumerate(windows):
            if index not in prediction_by_index:
                prediction_by_index[index] = self._predict(window)

        predictions = [prediction_by_index[index] for index in range(len(windows))]
        return predictions, len(predictions)

    def analyze(self, path: Path) -> AnalysisResult:
        audio, sr = load_audio(path, self.sample_rate)
        features = extract_audio_features(audio, sr)
        predictions, windows_analyzed = self._run_windows(audio, sr, features.duration_s)
        styles, genres, resolution = self._resolve_predictions(predictions)
        primary = genres[0] if genres else None

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
            windows_analyzed=windows_analyzed,
            device=self.classifier.resolved_device,
            analysis_mode=self.analysis_mode,
        )
