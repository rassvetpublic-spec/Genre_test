from __future__ import annotations

from .models import AnalysisResult


def version_comparability(
    left: AnalysisResult,
    right: AnalysisResult,
) -> tuple[bool, str]:
    """Return whether two stored runs have comparable genre verdicts."""
    if left.input_quality == "INSUFFICIENT_AUDIO" or right.input_quality == "INSUFFICIENT_AUDIO":
        return False, "genre verdict unavailable because short-input QC marks audio insufficient"
    if left.resolved_genre is None or right.resolved_genre is None:
        return False, "one side has no resolved genre verdict"
    return True, ""
