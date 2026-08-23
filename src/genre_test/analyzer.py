from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

from . import __version__
from .aggregate import aggregate_predictions
from .analysis_policy import (
    ANALYSIS_MODES,
    duration_window_target,
    input_quality_for_duration,
    needs_more_auto_windows,
    spread_indices,
)
from .audio import load_audio, select_windows
from .cancellation import CancelCheck, check_cancel
from .features import extract_audio_features
from .maest import DEFAULT_MODEL, MaestClassifier
from .models import AnalysisResult, AudioFeatures, StyleScore
from .performance import (
    append_perf,
    clock,
    elapsed_seconds,
    milliseconds,
    realtime_factor,
    realtime_speed,
)
from .resolver import GenreResolution, resolve_genre
from .runtime_meta import RESULT_SCHEMA_VERSION, current_git_commit, new_run_id, utc_now_iso
from .track_identity import identify_track


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
        init_started = clock()
        self.classifier = MaestClassifier(model_id=model_id, revision=revision, device=device)
        append_perf(
            "analyzer_init",
            analyzer_version=__version__,
            model_id=self.classifier.model_id,
            model_revision=self.classifier.revision,
            requested_device=device,
            resolved_device=self.classifier.resolved_device,
            elapsed_ms=milliseconds(elapsed_seconds(init_started)),
        )

    def _predict(
        self,
        window,
        cancel_check: CancelCheck | None = None,
        *,
        perf_samples: list[float] | None = None,
        perf_context: str | None = None,
        window_index: int | None = None,
    ) -> list[dict[str, float | str]]:
        # Never interrupt the model call itself. Observe cancellation immediately before and
        # immediately after one inference window so CUDA/PyTorch can leave the step cleanly.
        check_cancel(cancel_check)
        started = clock()
        try:
            prediction = self.classifier.predict(window, top_k=self.internal_top_k)
        except Exception:
            duration = elapsed_seconds(started)
            if perf_samples is not None:
                perf_samples.append(duration)
            append_perf(
                "maest_window",
                context=perf_context or "unknown",
                window_index=window_index,
                status="error",
                elapsed_ms=milliseconds(duration),
                device=self.classifier.resolved_device,
            )
            raise
        duration = elapsed_seconds(started)
        if perf_samples is not None:
            perf_samples.append(duration)
        append_perf(
            "maest_window",
            context=perf_context or "unknown",
            window_index=window_index,
            status="ok",
            elapsed_ms=milliseconds(duration),
            device=self.classifier.resolved_device,
        )
        check_cancel(cancel_check)
        return prediction

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
        *,
        perf_samples: list[float] | None = None,
        perf_context: str | None = None,
    ) -> tuple[
        dict[int, list[dict[str, float | str]]],
        Callable[[int], list[dict[str, float | str]]],
    ]:
        cache: dict[int, list[dict[str, float | str]]] = {}

        def get(index: int) -> list[dict[str, float | str]]:
            check_cancel(cancel_check)
            if index not in cache:
                cache[index] = self._predict(
                    windows[index],
                    cancel_check,
                    perf_samples=perf_samples,
                    perf_context=perf_context,
                    window_index=index,
                )
            check_cancel(cancel_check)
            return cache[index]

        return cache, get

    def _predict_windows(
        self,
        windows,
        cancel_check: CancelCheck | None = None,
        *,
        perf_samples: list[float] | None = None,
        perf_context: str | None = None,
    ) -> list[list[dict[str, float | str]]]:
        predictions: list[list[dict[str, float | str]]] = []
        for index, window in enumerate(windows):
            check_cancel(cancel_check)
            predictions.append(
                self._predict(
                    window,
                    cancel_check,
                    perf_samples=perf_samples,
                    perf_context=perf_context,
                    window_index=index,
                )
            )
        return predictions

    def _log_track_performance(
        self,
        *,
        path: Path,
        mode: str,
        audio_duration_s: float,
        total_s: float,
        stages: dict[str, float],
        inference_samples: list[float],
        windows_analyzed: int,
        unique_inference_windows: int,
        logical_window_uses: int,
        input_quality: str,
        auto_expanded: bool = False,
    ) -> None:
        inference_total_s = sum(inference_samples)
        append_perf(
            "track",
            path=path,
            mode=mode,
            input_quality=input_quality,
            device=self.classifier.resolved_device,
            audio_duration_s=round(audio_duration_s, 3),
            total_ms=milliseconds(total_s),
            load_ms=milliseconds(stages.get("load", 0.0)),
            features_ms=milliseconds(stages.get("features", 0.0)),
            identity_ms=milliseconds(stages.get("identity", 0.0)),
            select_windows_ms=milliseconds(stages.get("select_windows", 0.0)),
            auto_decision_ms=milliseconds(stages.get("auto_decision", 0.0)),
            build_result_ms=milliseconds(stages.get("build_result", 0.0)),
            inference_total_ms=milliseconds(inference_total_s),
            inference_avg_ms=milliseconds(
                inference_total_s / len(inference_samples) if inference_samples else 0.0
            ),
            inference_max_ms=milliseconds(max(inference_samples) if inference_samples else 0.0),
            windows_analyzed=windows_analyzed,
            unique_inference_windows=unique_inference_windows,
            logical_window_uses=logical_window_uses,
            cache_reused_window_uses=max(0, logical_window_uses - unique_inference_windows),
            auto_expanded=auto_expanded,
            realtime_factor=realtime_factor(total_s, audio_duration_s),
            realtime_speed_x=realtime_speed(total_s, audio_duration_s),
        )

    def analyze(
        self,
        path: Path,
        analysis_mode: str | None = None,
        track_id: str | None = None,
        cancel_check: CancelCheck | None = None,
    ) -> AnalysisResult:
        total_started = clock()
        stages: dict[str, float] = {}
        inference_samples: list[float] = []
        auto_expanded = False
        mode = (analysis_mode or self.analysis_mode).lower().strip()
        if mode not in ANALYSIS_MODES:
            raise ValueError(f"Unknown analysis mode: {mode}")

        check_cancel(cancel_check)
        resolved_path = path.resolve()

        started = clock()
        audio, sr = load_audio(resolved_path, self.sample_rate)
        stages["load"] = elapsed_seconds(started)
        check_cancel(cancel_check)

        started = clock()
        features = extract_audio_features(audio, sr)
        stages["features"] = elapsed_seconds(started)
        check_cancel(cancel_check)

        started = clock()
        identity = identify_track(resolved_path) if track_id is None else None
        resolved_track_id = track_id or identity.track_id
        source_file_size = identity.size_bytes if identity else resolved_path.stat().st_size
        stages["identity"] = elapsed_seconds(started)
        check_cancel(cancel_check)
        input_quality, quality_notes = input_quality_for_duration(features.duration_s)

        if input_quality == "INSUFFICIENT_AUDIO":
            started = clock()
            result = self._build_result(
                resolved_path,
                features,
                [],
                mode,
                resolved_track_id,
                source_file_size,
                input_quality,
                quality_notes,
            )
            stages["build_result"] = elapsed_seconds(started)
            total_s = elapsed_seconds(total_started)
            self._log_track_performance(
                path=resolved_path,
                mode=mode,
                audio_duration_s=features.duration_s,
                total_s=total_s,
                stages=stages,
                inference_samples=inference_samples,
                windows_analyzed=0,
                unique_inference_windows=0,
                logical_window_uses=0,
                input_quality=input_quality,
            )
            return result

        target = duration_window_target(features.duration_s)
        started = clock()
        if mode == "expert":
            windows = select_windows(audio, sr, self.window_seconds, self.window_count)
        else:
            windows = select_windows(audio, sr, self.window_seconds, target)
        stages["select_windows"] = elapsed_seconds(started)

        context = f"single:{mode}:{resolved_path.name}"
        if mode == "expert":
            predictions = self._predict_windows(
                windows,
                cancel_check,
                perf_samples=inference_samples,
                perf_context=context,
            )
        elif mode == "fast":
            indices = spread_indices(len(windows), min(len(windows), 3))
            predictions = [
                self._predict(
                    windows[index],
                    cancel_check,
                    perf_samples=inference_samples,
                    perf_context=context,
                    window_index=index,
                )
                for index in indices
            ]
        elif mode == "accurate" or len(windows) <= 5:
            predictions = self._predict_windows(
                windows,
                cancel_check,
                perf_samples=inference_samples,
                perf_context=context,
            )
        else:
            initial_indices = spread_indices(len(windows), 5)
            cache, get = self._prediction_cache(
                windows,
                cancel_check,
                perf_samples=inference_samples,
                perf_context=context,
            )
            initial_predictions = [get(index) for index in initial_indices]
            started = clock()
            _, _, resolution = self._resolve_predictions(initial_predictions)
            stages["auto_decision"] = elapsed_seconds(started)
            check_cancel(cancel_check)
            if needs_more_auto_windows(resolution.classification, resolution.confidence):
                auto_expanded = True
                predictions = [get(index) for index in range(len(windows))]
            else:
                predictions = initial_predictions
            del cache

        check_cancel(cancel_check)
        started = clock()
        result = self._build_result(
            resolved_path,
            features,
            predictions,
            mode,
            resolved_track_id,
            source_file_size,
            input_quality,
            quality_notes,
        )
        stages["build_result"] = elapsed_seconds(started)
        total_s = elapsed_seconds(total_started)
        self._log_track_performance(
            path=resolved_path,
            mode=mode,
            audio_duration_s=features.duration_s,
            total_s=total_s,
            stages=stages,
            inference_samples=inference_samples,
            windows_analyzed=len(predictions),
            unique_inference_windows=len(inference_samples),
            logical_window_uses=len(predictions),
            input_quality=input_quality,
            auto_expanded=auto_expanded,
        )
        return result

    def analyze_modes(
        self,
        path: Path,
        modes: Iterable[str] = ("fast", "auto", "accurate"),
        track_id: str | None = None,
        cancel_check: CancelCheck | None = None,
    ) -> dict[str, AnalysisResult]:
        total_started = clock()
        stages: dict[str, float] = {}
        inference_samples: list[float] = []
        auto_expanded = False
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

        started = clock()
        audio, sr = load_audio(resolved_path, self.sample_rate)
        stages["load"] = elapsed_seconds(started)
        check_cancel(cancel_check)

        started = clock()
        features = extract_audio_features(audio, sr)
        stages["features"] = elapsed_seconds(started)
        check_cancel(cancel_check)

        started = clock()
        identity = identify_track(resolved_path) if track_id is None else None
        resolved_track_id = track_id or identity.track_id
        source_file_size = identity.size_bytes if identity else resolved_path.stat().st_size
        stages["identity"] = elapsed_seconds(started)
        check_cancel(cancel_check)
        input_quality, quality_notes = input_quality_for_duration(features.duration_s)
        mode_label = "+".join(requested)

        if input_quality == "INSUFFICIENT_AUDIO":
            started = clock()
            results = {
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
            stages["build_result"] = elapsed_seconds(started)
            total_s = elapsed_seconds(total_started)
            self._log_track_performance(
                path=resolved_path,
                mode=mode_label,
                audio_duration_s=features.duration_s,
                total_s=total_s,
                stages=stages,
                inference_samples=inference_samples,
                windows_analyzed=0,
                unique_inference_windows=0,
                logical_window_uses=0,
                input_quality=input_quality,
            )
            return results

        target = duration_window_target(features.duration_s)
        started = clock()
        windows = select_windows(audio, sr, self.window_seconds, target)
        stages["select_windows"] = elapsed_seconds(started)
        cache, get = self._prediction_cache(
            windows,
            cancel_check,
            perf_samples=inference_samples,
            perf_context=f"multi:{mode_label}:{resolved_path.name}",
        )
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
                started = clock()
                _, _, resolution = self._resolve_predictions(initial_predictions)
                stages["auto_decision"] = elapsed_seconds(started)
                check_cancel(cancel_check)
                if needs_more_auto_windows(resolution.classification, resolution.confidence):
                    auto_expanded = True
                    result_predictions["auto"] = [get(index) for index in range(len(windows))]
                else:
                    result_predictions["auto"] = initial_predictions

        if "accurate" in requested:
            result_predictions["accurate"] = [get(index) for index in range(len(windows))]

        check_cancel(cancel_check)
        unique_inference_windows = len(cache)
        logical_window_uses = sum(len(predictions) for predictions in result_predictions.values())
        started = clock()
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
        stages["build_result"] = elapsed_seconds(started)
        del cache
        check_cancel(cancel_check)
        total_s = elapsed_seconds(total_started)
        self._log_track_performance(
            path=resolved_path,
            mode=mode_label,
            audio_duration_s=features.duration_s,
            total_s=total_s,
            stages=stages,
            inference_samples=inference_samples,
            windows_analyzed=logical_window_uses,
            unique_inference_windows=unique_inference_windows,
            logical_window_uses=logical_window_uses,
            input_quality=input_quality,
            auto_expanded=auto_expanded,
        )
        return results
