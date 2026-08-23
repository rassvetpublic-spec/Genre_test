from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

from . import __version__
from .aggregate import aggregate_predictions
from .analysis_policy import (
    ANALYSIS_MODES,
    duration_window_target,
    needs_more_auto_windows,
    spread_indices,
)
from .audio import load_audio, select_windows
from .cancellation import CancelCheck, check_cancel
from .features import extract_audio_features
from .maest import DEFAULT_MODEL, MaestClassifier
from .models import AnalysisResult, AudioFeatures, StyleScore
from .resolver import GenreResolution, resolve_genre
from .runtime_meta import RESULT_SCHEMA_VERSION, current_git_commit, new_run_id, utc_now_iso
from .track_identity import identify_track

INSUFFICIENT_AUDIO_SECONDS = 10.0
SHORT_AUDIO_SECONDS = 30.0


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
        self.internal_top_k = max(25, top_k)
        self.analysis_mode = mode
        self.git_commit = current_git_commit()
        self.classifier = MaestClassifier(model_id=model_id, revision=revision, device=device)

    def _predict(
        self,
        window,
        cancel_check: CancelCheck | None = None,
    ) -> list[dict[str, float | str]]:
        # Never interrupt the model call itself. Observe cancellation immediately before and
        # immediately after one inference window so CUDA/PyTorch can leave the step cleanly.
        check_cancel(cancel_check)
        prediction = self.classifier.predict(window, top_k=self.internal_top_k)
        check_cancel(cancel_check)
        return prediction

    @staticmethod
    def _input_quality(duration_s: float) -> tuple[str, tuple[str, ...]]:
        if duration_s < INSUFFICIENT_AUDIO_SECONDS:
            return (
                "INSUFFICIENT_AUDIO",
                (
                    f"duration {duration_s:.2f}s is below the {INSUFFICIENT_AUDIO_SECONDS:.0f}s "
                    "minimum for a genre verdict",
                ),
            )
        if duration_s < SHORT_AUDIO_SECONDS:
            return (
                "SHORT_INPUT",
                (
                    f"duration {duration_s:.2f}s is shorter than one full "
                    f"{SHORT_AUDIO_SECONDS:.0f}s MAEST window; confidence is capped at medium",
                ),
            )
        return "NORMAL", ()

    def _resolve_predictions(
        self, predictions: list[list[dict[str, float | str]]]
    ) -> tuple[list[StyleScore], list[StyleScore], GenreResolution]:
        styles, genres = aggregate_predictions(predictions, top_k=self.top_k)
        return styles, genres, resolve_genre(styles, genres)

    def _build_result(
        self,
        path: Path,
        features: AudioFeatures,
        predictions: list[list[dict[str, float | str]]],
        mode: str,
        track_id: str,
        source_file_size: int,
        input_quality: str = "NORMAL",
        quality_notes: tuple[str, ...] = (),
    ) -> AnalysisResult:
        if input_quality == "INSUFFICIENT_AUDIO":
            styles: list[StyleScore] = []
            genres: list[StyleScore] = []
            resolution = GenreResolution(
                resolved_genre=None,
                classification="insufficient_audio",
                confidence="low",
                family_margin=None,
                family_ratio=None,
                style_margin=None,
                primary_family=None,
                secondary_family=None,
                secondary_style=None,
            )
        else:
            styles, genres, resolution = self._resolve_predictions(predictions)

        primary = genres[0] if genres else None
        confidence = resolution.confidence
        if input_quality == "SHORT_INPUT" and confidence == "high":
            confidence = "medium"

        return AnalysisResult(
            path=str(path.resolve()),
            primary_genre=primary.label if primary else None,
            primary_genre_score=round(primary.score, 6) if primary else None,
            resolved_genre=resolution.resolved_genre,
            classification=resolution.classification,
            confidence=confidence,
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
            windows_analyzed=len(predictions),
            device=self.classifier.resolved_device,
            analysis_mode=mode,
            schema_version=RESULT_SCHEMA_VERSION,
            analyzer_version=__version__,
            run_id=new_run_id(),
            analyzed_at=utc_now_iso(),
            track_id=track_id,
            window_seconds=self.window_seconds,
            internal_top_k=self.internal_top_k,
            report_top_k=self.top_k,
            git_commit=self.git_commit,
            source_file_size=source_file_size,
            input_quality=input_quality,
            quality_notes=quality_notes,
        )

    def _prediction_cache(
        self,
        windows,
        cancel_check: CancelCheck | None = None,
    ) -> tuple[
        dict[int, list[dict[str, float | str]]],
        Callable[[int], list[dict[str, float | str]]],
    ]:
        cache: dict[int, list[dict[str, float | str]]] = {}

        def get(index: int) -> list[dict[str, float | str]]:
            check_cancel(cancel_check)
            if index not in cache:
                cache[index] = self._predict(windows[index], cancel_check)
            check_cancel(cancel_check)
            return cache[index]

        return cache, get

    def _predict_windows(
        self,
        windows,
        cancel_check: CancelCheck | None = None,
    ) -> list[list[dict[str, float | str]]]:
        predictions: list[list[dict[str, float | str]]] = []
        for window in windows:
            check_cancel(cancel_check)
            predictions.append(self._predict(window, cancel_check))
        return predictions

    def analyze(
        self,
        path: Path,
        analysis_mode: str | None = None,
        track_id: str | None = None,
        cancel_check: CancelCheck | None = None,
    ) -> AnalysisResult:
        mode = (analysis_mode or self.analysis_mode).lower().strip()
        if mode not in ANALYSIS_MODES:
            raise ValueError(f"Unknown analysis mode: {mode}")

        check_cancel(cancel_check)
        resolved_path = path.resolve()
        audio, sr = load_audio(resolved_path, self.sample_rate)
        check_cancel(cancel_check)
        features = extract_audio_features(audio, sr)
        check_cancel(cancel_check)
        identity = identify_track(resolved_path) if track_id is None else None
        check_cancel(cancel_check)
        resolved_track_id = track_id or identity.track_id
        source_file_size = identity.size_bytes if identity else resolved_path.stat().st_size
        input_quality, quality_notes = self._input_quality(features.duration_s)

        if input_quality == "INSUFFICIENT_AUDIO":
            return self._build_result(
                resolved_path,
                features,
                [],
                mode,
                resolved_track_id,
                source_file_size,
                input_quality,
                quality_notes,
            )

        target = duration_window_target(features.duration_s)
        if mode == "expert":
            windows = select_windows(audio, sr, self.window_seconds, self.window_count)
            predictions = self._predict_windows(windows, cancel_check)
        else:
            windows = select_windows(audio, sr, self.window_seconds, target)
            if mode == "fast":
                indices = spread_indices(len(windows), min(len(windows), 3))
                predictions = [self._predict(windows[index], cancel_check) for index in indices]
            elif mode == "accurate" or len(windows) <= 5:
                predictions = self._predict_windows(windows, cancel_check)
            else:
                initial_indices = spread_indices(len(windows), 5)
                cache, get = self._prediction_cache(windows, cancel_check)
                initial_predictions = [get(index) for index in initial_indices]
                _, _, resolution = self._resolve_predictions(initial_predictions)
                check_cancel(cancel_check)
                if needs_more_auto_windows(resolution.classification, resolution.confidence):
                    predictions = [get(index) for index in range(len(windows))]
                else:
                    predictions = initial_predictions
                del cache

        check_cancel(cancel_check)
        return self._build_result(
            resolved_path,
            features,
            predictions,
            mode,
            resolved_track_id,
            source_file_size,
            input_quality,
            quality_notes,
        )

    def analyze_modes(
        self,
        path: Path,
        modes: Iterable[str] = ("fast", "auto", "accurate"),
        track_id: str | None = None,
        cancel_check: CancelCheck | None = None,
    ) -> dict[str, AnalysisResult]:
        requested = list(dict.fromkeys(mode.lower().strip() for mode in modes))
        if not requested:
            raise ValueError("At least one analysis mode is required")
        if any(mode not in ANALYSIS_MODES for mode in requested):
            invalid = [mode for mode in requested if mode not in ANALYSIS_MODES]
            raise ValueError(f"Unknown analysis modes: {invalid}")
        if "expert" in requested:
            raise ValueError("analyze_modes does not combine expert mode with automatic modes")

        check_cancel(cancel_check)
        resolved_path = path.resolve()
        audio, sr = load_audio(resolved_path, self.sample_rate)
        check_cancel(cancel_check)
        features = extract_audio_features(audio, sr)
        check_cancel(cancel_check)
        identity = identify_track(resolved_path) if track_id is None else None
        check_cancel(cancel_check)
        resolved_track_id = track_id or identity.track_id
        source_file_size = identity.size_bytes if identity else resolved_path.stat().st_size
        input_quality, quality_notes = self._input_quality(features.duration_s)

        if input_quality == "INSUFFICIENT_AUDIO":
            return {
                mode: self._build_result(
                    resolved_path,
                    features,
                    [],
                    mode,
                    resolved_track_id,
                    source_file_size,
                    input_quality,
                    quality_notes,
                )
                for mode in requested
            }

        target = duration_window_target(features.duration_s)
        windows = select_windows(audio, sr, self.window_seconds, target)
        cache, get = self._prediction_cache(windows, cancel_check)
        result_predictions: dict[str, list[list[dict[str, float | str]]]] = {}

        if "fast" in requested:
            fast_indices = spread_indices(len(windows), min(len(windows), 3))
            result_predictions["fast"] = [get(index) for index in fast_indices]

        if "auto" in requested:
            if len(windows) <= 5:
                auto_indices = list(range(len(windows)))
                result_predictions["auto"] = [get(index) for index in auto_indices]
            else:
                initial_indices = spread_indices(len(windows), 5)
                initial_predictions = [get(index) for index in initial_indices]
                _, _, resolution = self._resolve_predictions(initial_predictions)
                check_cancel(cancel_check)
                if needs_more_auto_windows(resolution.classification, resolution.confidence):
                    result_predictions["auto"] = [get(index) for index in range(len(windows))]
                else:
                    result_predictions["auto"] = initial_predictions

        if "accurate" in requested:
            result_predictions["accurate"] = [get(index) for index in range(len(windows))]

        check_cancel(cancel_check)
        results = {
            mode: self._build_result(
                resolved_path,
                features,
                result_predictions[mode],
                mode,
                resolved_track_id,
                source_file_size,
                input_quality,
                quality_notes,
            )
            for mode in requested
        }
        del cache
        check_cancel(cancel_check)
        return results
