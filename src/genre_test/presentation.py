from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .models import AnalysisResult

if TYPE_CHECKING:
    from .validation import ValidationSessionResult

PROFILE_VIEWS = {"normal", "suno", "distributor"}


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


def _format_profile_normal(result: AnalysisResult, top_n: int) -> str:
    profile = result.audio_profile
    assert profile is not None
    lines = [
        Path(result.path).name,
        "",
        f"Genre: {profile.primary_genre or 'n/a'}",
        f"Family: {profile.broad_family or 'n/a'}",
        f"Confidence: {profile.confidence}",
    ]
    if profile.secondary_influence:
        lines.append(f"Secondary influence: {profile.secondary_influence}")
    if profile.adjacent_genres:
        lines.append("Adjacent: " + ", ".join(profile.adjacent_genres))
    if profile.vocal:
        lines.append(f"Vocal: {profile.vocal}")
    if profile.instruments:
        lines.append("Instrumentation: " + ", ".join(profile.instruments))
    if profile.moods:
        lines.append("Mood: " + ", ".join(profile.moods))
    if profile.production:
        lines.append("Production: " + ", ".join(profile.production))
    if result.input_quality != "NORMAL":
        lines.append(f"Input quality: {result.input_quality}")
        if result.quality_notes:
            lines.append("QC: " + "; ".join(result.quality_notes))
    lines.extend(
        [
            f"Tempo: {tempo_candidates(result.audio_features.bpm)}",
            f"Key: {result.audio_features.key or 'n/a'} {result.audio_features.mode or ''}".rstrip(),
            f"Analysis: {result.analysis_mode} | MAEST windows: {result.windows_analyzed}",
            "",
            "Scores:",
            *_score_table(result, top_n=top_n),
        ]
    )
    return "\n".join(lines)


def _format_profile_suno(result: AnalysisResult) -> str:
    profile = result.audio_profile
    assert profile is not None
    lines = [Path(result.path).name, "", "SUNO Style of Music:", profile.suno_style or "n/a"]
    if profile.primary_genre:
        lines.append(f"Primary: {profile.primary_genre}")
    if profile.secondary_influence:
        lines.append(f"Influence: {profile.secondary_influence}")
    if profile.vocal:
        lines.append(f"Vocal: {profile.vocal}")
    if profile.instruments:
        lines.append("Instruments: " + ", ".join(profile.instruments))
    if profile.moods:
        lines.append("Mood: " + ", ".join(profile.moods))
    lines.extend(
        [
            f"Tempo: {tempo_candidates(result.audio_features.bpm)}",
            f"Key: {result.audio_features.key or 'n/a'} {result.audio_features.mode or ''}".rstrip(),
        ]
    )
    return "\n".join(lines)


def _format_profile_distributor(result: AnalysisResult) -> str:
    profile = result.audio_profile
    assert profile is not None
    lines = [
        Path(result.path).name,
        "",
        f"Distributor genre: {profile.distributor_genre or 'n/a'}",
        f"Distributor subgenre: {profile.distributor_subgenre or 'n/a'}",
        f"Primary genre: {profile.primary_genre or 'n/a'}",
        f"Confidence: {profile.confidence}",
    ]
    if profile.secondary_influence:
        lines.append(f"Secondary influence: {profile.secondary_influence}")
    if profile.adjacent_genres:
        lines.append("Adjacent: " + ", ".join(profile.adjacent_genres))
    return "\n".join(lines)


def format_result_text(
    result: AnalysisResult,
    top_n: int = 10,
    *,
    detailed: bool = False,
    view: str = "normal",
) -> str:
    normalized_view = view.lower().strip()
    if normalized_view not in PROFILE_VIEWS:
        raise ValueError(f"Unknown presentation view: {view}")

    if result.audio_profile is not None and not detailed:
        if normalized_view == "suno":
            return _format_profile_suno(result)
        if normalized_view == "distributor":
            return _format_profile_distributor(result)
        return _format_profile_normal(result, top_n)

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
        if result.semantic_evidence is not None:
            semantic = result.semantic_evidence
            lines.extend(
                [
                    f"Semantic status: {semantic.status}",
                    f"Semantic model: {semantic.model_id}",
                    f"Semantic revision: {semantic.model_revision or 'un-pinned'}",
                    f"Semantic device/windows: {semantic.device} / {semantic.windows_analyzed}",
                    f"Semantic genres: {_score_list(semantic.genre_tags, 8)}",
                    f"Semantic vocals: {_score_list(semantic.vocal_tags, 5)}",
                    f"Semantic instruments: {_score_list(semantic.instrument_tags, 8)}",
                    f"Semantic moods: {_score_list(semantic.mood_tags, 5)}",
                ]
            )
        if result.audio_profile is not None:
            profile = result.audio_profile
            profile_primary_line = (
                f"Profile primary/family: {profile.primary_genre or 'n/a'} / "
                f"{profile.broad_family or 'n/a'}"
            )
            profile_confidence_line = (
                f"Profile confidence/agreement: {profile.confidence} / "
                f"{profile.ensemble_agreement}"
            )
            lines.extend(
                [
                    profile_primary_line,
                    profile_confidence_line,
                    "Profile family evidence: " + _score_list(profile.family_evidence, 8),
                ]
            )

    lines.extend(["", "Scores:", *_score_table(result, top_n=top_n)])
    return "\n".join(lines)


def _score_list(items, limit: int) -> str:
    selected = list(items[:limit])
    if not selected:
        return "n/a"
    return "; ".join(f"{item.label}={item.score:.4f}" for item in selected)


def format_validation_run_metadata(result: ValidationSessionResult) -> str:
    """Full per-run internals for the Validation / Перепроверка tab only."""
    lines = ["Detailed run metadata:"]
    for outcome in result.outcomes:
        lines.extend(
            [
                "",
                f"[{outcome.severity}] {Path(outcome.path).name}",
                f"track_id: {outcome.track_id}",
                f"status: {outcome.status}",
            ]
        )
        for mode, item in outcome.results.items():
            family_score = (
                f"{item.primary_genre_score:.4f}"
                if item.primary_genre_score is not None
                else "n/a"
            )
            summary_line = (
                f"    genre={item.resolved_genre or 'n/a'} | "
                f"family={item.primary_genre or 'n/a'} ({family_score}) | "
                f"classification={item.classification} | confidence={item.confidence}"
            )
            runtime_line = (
                f"    quality={item.input_quality} | windows={item.windows_analyzed} | "
                f"device={item.device}"
            )
            lines.extend(
                [
                    f"  [{mode}]",
                    summary_line,
                    runtime_line,
                    f"    analyzer={item.analyzer_version} | schema={item.schema_version}",
                    f"    run_id={item.run_id or 'n/a'}",
                    f"    track_id={item.track_id or outcome.track_id}",
                    f"    MAEST={item.model_id} @ {item.model_revision or 'un-pinned'}",
                    f"    top_styles: {_score_list(item.top_styles, 5)}",
                    f"    broad_families: {_score_list(item.broad_genres, 6)}",
                ]
            )
            if item.secondary_style or item.secondary_genre:
                lines.append(
                    f"    alternative: style={item.secondary_style or 'n/a'} | "
                    f"family={item.secondary_genre or 'n/a'}"
                )
            if item.semantic_evidence is not None:
                semantic = item.semantic_evidence
                semantic_model_line = (
                    f"    semantic={semantic.model_id} @ "
                    f"{semantic.model_revision or 'un-pinned'}"
                )
                lines.extend(
                    [
                        f"    semantic_status={semantic.status}",
                        semantic_model_line,
                        f"    semantic_genres: {_score_list(semantic.genre_tags, 8)}",
                        f"    semantic_vocals: {_score_list(semantic.vocal_tags, 5)}",
                        f"    semantic_instruments: {_score_list(semantic.instrument_tags, 8)}",
                        f"    semantic_moods: {_score_list(semantic.mood_tags, 5)}",
                    ]
                )
            if item.audio_profile is not None:
                profile = item.audio_profile
                profile_line = (
                    f"    profile={profile.primary_genre or 'n/a'} / "
                    f"{profile.broad_family or 'n/a'} / {profile.confidence}"
                )
                ensemble_line = (
                    f"    ensemble={profile.ensemble_agreement}; "
                    f"sources={','.join(profile.ensemble_sources)}"
                )
                lines.extend(
                    [
                        profile_line,
                        ensemble_line,
                        f"    family_evidence: {_score_list(profile.family_evidence, 8)}",
                    ]
                )
            if item.quality_notes:
                lines.append("    QC: " + "; ".join(item.quality_notes))
    return "\n".join(lines)
