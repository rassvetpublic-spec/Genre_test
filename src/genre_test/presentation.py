from __future__ import annotations

from pathlib import Path

from .models import AnalysisResult


def tempo_candidates(bpm: float | None) -> str:
    if not bpm:
        return "n/a"
    half = bpm / 2.0
    double = bpm * 2.0
    return f"{bpm:.2f} BPM  |  half {half:.2f}  |  double {double:.2f}"


def _score_table(result: AnalysisResult, top_n: int = 10, broad_n: int = 6) -> list[str]:
    styles = result.top_styles[:top_n]
    families = result.broad_genres[:broad_n]
    rows = max(len(styles), len(families))
    if rows == 0:
        return ["Scores: n/a"]

    style_width = max(9, *(len(item.label) for item in styles)) if styles else 9
    family_width = max(12, *(len(item.label) for item in families)) if families else 12
    style_width = min(style_width, 40)
    family_width = min(family_width, 28)

    header = (
        f"{'#':>2}  {'Top style':<{style_width}}  {'Score':>7}  |  "
        f"{'Broad family':<{family_width}}  {'Score':>7}"
    )
    divider = "-" * len(header)
    lines = [header, divider]
    for index in range(rows):
        style = styles[index] if index < len(styles) else None
        family = families[index] if index < len(families) else None
        style_label = style.label[:style_width] if style else ""
        style_score = f"{style.score:.4f}" if style else ""
        family_label = family.label[:family_width] if family else ""
        family_score = f"{family.score:.4f}" if family else ""
        lines.append(
            f"{index + 1:>2}  {style_label:<{style_width}}  {style_score:>7}  |  "
            f"{family_label:<{family_width}}  {family_score:>7}"
        )
    return lines


def format_result_text(
    result: AnalysisResult,
    top_n: int = 10,
    *,
    detailed: bool = False,
) -> str:
    genre = result.resolved_genre or "n/a"
    family = result.primary_genre or "n/a"
    family_score = (
        f" ({result.primary_genre_score:.3f})"
        if result.primary_genre_score is not None
        else ""
    )
    lines = [
        Path(result.path).name,
        "",
        f"Genre: {genre}",
        f"Family: {family}{family_score}",
        f"Classification: {result.classification} | Confidence: {result.confidence}",
    ]

    if result.secondary_genre or result.secondary_style:
        secondary_bits: list[str] = []
        if result.secondary_style:
            secondary_bits.append(f"style={result.secondary_style}")
        if result.secondary_genre:
            secondary_bits.append(f"family={result.secondary_genre}")
        lines.append("Alternative: " + " | ".join(secondary_bits))

    if result.input_quality != "NORMAL":
        lines.append(f"Input quality: {result.input_quality}")
        if result.quality_notes:
            lines.append("QC: " + "; ".join(result.quality_notes))

    lines.extend(
        [
            f"Tempo: {tempo_candidates(result.audio_features.bpm)}",
            f"Key: {result.audio_features.key or 'n/a'} {result.audio_features.mode or ''}".rstrip(),
            f"Analysis: {result.analysis_mode} | Windows: {result.windows_analyzed}",
        ]
    )

    if detailed:
        lines.extend(
            [
                f"Analyzer version: {result.analyzer_version} | Schema: {result.schema_version}",
                f"Run ID: {result.run_id or 'n/a'}",
                f"Track ID: {result.track_id or 'n/a'}",
                f"MAEST model: {result.model_id}",
                f"MAEST revision: {result.model_revision or 'un-pinned'}",
                f"Device: {result.device}",
            ]
        )
        if result.family_margin is not None:
            lines.append(f"Family margin: {result.family_margin:.3f}")
        if result.family_ratio is not None:
            lines.append(f"Secondary/primary family ratio: {result.family_ratio:.3f}")
        if result.style_margin is not None:
            lines.append(f"Relative style margin: {result.style_margin:.3f}")

    lines.extend(["", "Scores:", *_score_table(result, top_n=top_n)])
    return "\n".join(lines)
