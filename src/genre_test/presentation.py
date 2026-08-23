from __future__ import annotations

from pathlib import Path

from .models import AnalysisResult


def tempo_candidates(bpm: float | None) -> str:
    if not bpm:
        return "n/a"
    half = bpm / 2.0
    double = bpm * 2.0
    return f"{bpm:.2f} BPM  |  half {half:.2f}  |  double {double:.2f}"


def format_result_text(result: AnalysisResult, top_n: int = 10) -> str:
    lines = [
        Path(result.path).name,
        "",
        f"Input quality: {result.input_quality}",
        f"Resolved genre: {result.resolved_genre or 'n/a'}",
        f"Broad family: {result.primary_genre or 'n/a'}",
        f"Classification: {result.classification}",
        f"Confidence: {result.confidence}",
        f"Analysis: {result.analysis_mode} | Windows analyzed: {result.windows_analyzed}",
        f"Analyzer version: {result.analyzer_version} | Schema: {result.schema_version}",
        f"MAEST model: {result.model_id}",
        f"MAEST revision: {result.model_revision or 'un-pinned'}",
    ]
    if result.quality_notes:
        lines.append("QC: " + "; ".join(result.quality_notes))
    if result.run_id:
        lines.append(f"Run ID: {result.run_id}")
    if result.track_id:
        lines.append(f"Track ID: {result.track_id}")
    if result.secondary_genre:
        lines.append(f"Secondary family: {result.secondary_genre}")
    if result.secondary_style:
        lines.append(f"Alternative style: {result.secondary_style}")
    if result.family_margin is not None:
        lines.append(f"Family margin: {result.family_margin:.3f}")
    if result.family_ratio is not None:
        lines.append(f"Secondary/primary family ratio: {result.family_ratio:.3f}")
    if result.style_margin is not None:
        lines.append(f"Relative style margin: {result.style_margin:.3f}")
    lines.extend(
        [
            f"Tempo: {tempo_candidates(result.audio_features.bpm)}",
            f"Key: {result.audio_features.key or 'n/a'} {result.audio_features.mode or ''}".rstrip(),
            "",
            "Top styles:",
        ]
    )
    for idx, item in enumerate(result.top_styles[:top_n], 1):
        lines.append(f"{idx:>2}. {item.label:<36} {item.score:.4f}")

    lines.extend(["", "Broad families:"])
    for item in result.broad_genres[:6]:
        lines.append(f"- {item.label:<24} {item.score:.4f}")
    return "\n".join(lines)
