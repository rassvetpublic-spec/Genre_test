from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .analysis_policy import INSUFFICIENT_AUDIO_SECONDS
from .analyzer import GenreAnalyzer
from .audio import load_audio, select_windows
from .cancellation import CancelCheck, check_cancel
from .logging_utils import append_log
from .model_config import (
    DEFAULT_MODEL,
    DEFAULT_SEMANTIC_MODEL,
    DEFAULT_SEMANTIC_MODEL_REVISION,
    DEFAULT_SEMANTIC_WINDOW_COUNT,
    DEFAULT_SEMANTIC_WINDOW_SECONDS,
)
from .models import AnalysisResult, SemanticEvidence
from .performance import append_perf, clock, elapsed_seconds, milliseconds
from .profile import build_audio_profile
from .semantic import SemanticTagger

SEMANTIC_MODES = {"auto", "on", "off"}


class ProfileAnalyzer:
    """v0.4 facade: MAEST genre analysis plus independent AudioSet semantic evidence.

    The proven v0.3 GenreAnalyzer remains unchanged and continues to own raw
    genre/regression semantics. AudioProfile is layered on top so Validation can
    still compare the stable MAEST result while the user-facing profile uses the
    new ensemble evidence.
    """

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
        inference_batch_size: int | None = None,
        semantic_mode: str = "auto",
        semantic_model_id: str = DEFAULT_SEMANTIC_MODEL,
        semantic_revision: str | None = DEFAULT_SEMANTIC_MODEL_REVISION,
    ) -> None:
        normalized_semantic_mode = semantic_mode.lower().strip()
        if normalized_semantic_mode not in SEMANTIC_MODES:
            raise ValueError("semantic_mode must be auto, on or off")

        self.genre = GenreAnalyzer(
            model_id=model_id,
            revision=revision,
            device=device,
            sample_rate=sample_rate,
            window_seconds=window_seconds,
            window_count=window_count,
            top_k=top_k,
            analysis_mode=analysis_mode,
            inference_batch_size=inference_batch_size,
        )
        self.semantic_mode = normalized_semantic_mode
        self.semantic_model_id = semantic_model_id
        self.semantic_revision = semantic_revision
        self._semantic: SemanticTagger | None = None
        self._semantic_failure: str | None = None

    @property
    def sample_rate(self) -> int:
        return self.genre.sample_rate

    def _unavailable_evidence(self, reason: str) -> SemanticEvidence:
        return SemanticEvidence(
            model_id=self.semantic_model_id,
            model_revision=self.semantic_revision,
            device="unavailable",
            windows_analyzed=0,
            top_tags=[],
            genre_tags=[],
            mood_tags=[],
            vocal_tags=[],
            instrument_tags=[],
            production_tags=[],
            status="unavailable",
            notes=(reason,),
        )

    def _semantic_evidence(
        self,
        path: Path,
        duration_s: float,
        device: str,
        cancel_check: CancelCheck | None,
    ) -> SemanticEvidence | None:
        if self.semantic_mode == "off" or duration_s < INSUFFICIENT_AUDIO_SECONDS:
            return None
        if self._semantic_failure is not None:
            return self._unavailable_evidence(self._semantic_failure)

        check_cancel(cancel_check)
        started = clock()
        try:
            if self._semantic is None:
                self._semantic = SemanticTagger(
                    model_id=self.semantic_model_id,
                    revision=self.semantic_revision,
                    device=device,
                )
            audio, sr = load_audio(path, self.sample_rate)
            windows = select_windows(
                audio,
                sr,
                DEFAULT_SEMANTIC_WINDOW_SECONDS,
                DEFAULT_SEMANTIC_WINDOW_COUNT,
            )
            evidence = self._semantic.predict(
                windows,
                sr,
                cancel_check=cancel_check,
            )
            append_perf(
                "semantic_track",
                path=path,
                status="ok",
                windows=evidence.windows_analyzed,
                elapsed_ms=milliseconds(elapsed_seconds(started)),
            )
            return evidence
        except Exception as exc:
            if self.semantic_mode == "on":
                raise
            reason = f"{type(exc).__name__}: {exc}"
            self._semantic_failure = reason
            append_log(f"Semantic model unavailable; continuing MAEST-only: {reason}")
            append_perf(
                "semantic_track",
                path=path,
                status="unavailable",
                elapsed_ms=milliseconds(elapsed_seconds(started)),
                error_type=type(exc).__name__,
            )
            return self._unavailable_evidence(reason)

    def analyze(
        self,
        path: Path,
        analysis_mode: str | None = None,
        track_id: str | None = None,
        cancel_check: CancelCheck | None = None,
    ) -> AnalysisResult:
        result = self.genre.analyze(
            path,
            analysis_mode=analysis_mode,
            track_id=track_id,
            cancel_check=cancel_check,
        )
        check_cancel(cancel_check)
        evidence = self._semantic_evidence(
            Path(result.path),
            result.audio_features.duration_s,
            self.genre.classifier.resolved_device,
            cancel_check,
        )
        enriched = replace(result, semantic_evidence=evidence)
        profile = build_audio_profile(enriched, evidence)
        return replace(enriched, audio_profile=profile)
