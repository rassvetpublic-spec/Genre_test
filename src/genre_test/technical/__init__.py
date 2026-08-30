"""Backend-neutral technical audio quality measurements.

These measurements are deliberately independent from MAEST/AST/CLaMP genre
inference and from any specific mastering plug-in. They can be reused for
source, repair, stem, mastering, codec-preview, and A/B/X comparisons.
"""

from .mastering_metrics import (
    ALGORITHM_ID,
    CODEC_SPECS,
    MONO_BANDS,
    compare_mastering_arrays,
    compare_mastering_files,
    correlation_lr,
    detect_transient_events,
    measure_mono_loss,
    measure_transient_retention,
    overall_mono_retention,
)
from .temporal_structure import (
    ALGORITHM_ID as TEMPORAL_STRUCTURE_ALGORITHM_ID,
    TemporalStructureConfig,
    TemporalStructureProfileV1,
    analyze_temporal_structure,
)

__all__ = [
    "ALGORITHM_ID",
    "CODEC_SPECS",
    "MONO_BANDS",
    "TEMPORAL_STRUCTURE_ALGORITHM_ID",
    "TemporalStructureConfig",
    "TemporalStructureProfileV1",
    "analyze_temporal_structure",
    "compare_mastering_arrays",
    "compare_mastering_files",
    "correlation_lr",
    "detect_transient_events",
    "measure_mono_loss",
    "measure_transient_retention",
    "overall_mono_retention",
]
