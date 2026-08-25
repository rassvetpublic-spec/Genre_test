from __future__ import annotations

from pathlib import Path

from .build_history import BuildAwareHistoryDB, BuildInfo
from .comparison import SEVERITY_ORDER, compare_results
from .models import AnalysisResult
from .report import write_version_comparison_report


def _comparable(left: AnalysisResult, right: AnalysisResult) -> tuple[bool, str]:
    if left.input_quality == "INSUFFICIENT_AUDIO" or right.input_quality == "INSUFFICIENT_AUDIO":
        return False, "genre verdict unavailable because short-input QC marks audio insufficient"
    if left.resolved_genre is None or right.resolved_genre is None:
        return False, "one side has no resolved genre verdict"
    return True, ""


def compare_builds(
    history: BuildAwareHistoryDB,
    build_a: BuildInfo,
    build_b: BuildInfo,
    *,
    mode: str = "auto",
    out_dir: Path,
) -> tuple[dict[str, object], list[dict[str, object]], str, str]:
    rows: list[dict[str, object]] = []
    counts = {name: 0 for name in SEVERITY_ORDER}
    broad_matches = 0
    resolved_matches = 0
    tempo_equivalent = 0
    key_known = 0
    key_matches = 0
    comparable_total = 0
    not_comparable = 0

    for track_id in history.track_ids():
        selected_mode = None if mode == "any" else mode
        left = history.latest_run_for_build(track_id, build_a, selected_mode)
        right = history.latest_run_for_build(track_id, build_b, selected_mode)
        if not left or not right:
            continue

        is_comparable, reason = _comparable(left, right)
        base_row: dict[str, object] = {
            "track_id": track_id,
            "path": right.path or left.path,
            "left_mode": left.analysis_mode,
            "right_mode": right.analysis_mode,
            "left_quality": left.input_quality,
            "right_quality": right.input_quality,
            "left_genre": left.resolved_genre,
            "right_genre": right.resolved_genre,
            "left_family": left.primary_genre,
            "right_family": right.primary_genre,
            "comparable": is_comparable,
            "comparison_reason": reason,
        }
        if not is_comparable:
            not_comparable += 1
            rows.append(
                {
                    **base_row,
                    "severity": "NOT_COMPARABLE",
                    "tempo_relation": "not_comparable",
                    "js_divergence": "",
                    "cosine_similarity": "",
                    "topn_weighted_overlap": "",
                    "reasons": reason,
                }
            )
            continue

        comparison = compare_results(left, right)
        comparable_total += 1
        counts[comparison.severity] += 1
        broad_matches += int(comparison.broad_match)
        resolved_matches += int(comparison.resolved_match)
        tempo_equivalent += int(comparison.tempo_relation in {"same", "half-double"})
        if comparison.key_match is not None:
            key_known += 1
            key_matches += int(comparison.key_match)
        rows.append(
            {
                **base_row,
                "severity": comparison.severity,
                "tempo_relation": comparison.tempo_relation,
                "js_divergence": comparison.js_divergence,
                "cosine_similarity": comparison.cosine_similarity,
                "topn_weighted_overlap": comparison.topn_weighted_overlap,
                "reasons": "; ".join(comparison.reasons),
            }
        )

    def pct(value: int, denom: int) -> float:
        return round(100.0 * value / denom, 2) if denom else 0.0

    summary: dict[str, object] = {
        "version_a": build_a.label,
        "version_b": build_b.label,
        "build_key_a": build_a.key,
        "build_key_b": build_b.key,
        "mode": mode,
        "mode_warning": (
            "diagnostic any-mode comparison may pair different analysis modes"
            if mode == "any"
            else ""
        ),
        "tracks_considered": len(rows),
        "tracks_compared": comparable_total,
        "not_comparable_tracks": not_comparable,
        "severity_counts": counts,
        "broad_family_match_pct": pct(broad_matches, comparable_total),
        "resolved_genre_match_pct": pct(resolved_matches, comparable_total),
        "tempo_equivalent_pct": pct(tempo_equivalent, comparable_total),
        "key_mode_match_pct": pct(key_matches, key_known),
        "key_mode_known": key_known,
    }
    json_path, csv_path = write_version_comparison_report(summary, rows, out_dir)
    return summary, rows, str(json_path), str(csv_path)


def format_build_comparison(
    summary: dict[str, object],
    rows: list[dict[str, object]],
    json_report: str,
    csv_report: str,
) -> str:
    counts = summary["severity_counts"]
    lines = [
        f"Builds: {summary['version_a']} -> {summary['version_b']} ({summary['mode']})",
        f"Tracks considered: {summary['tracks_considered']}",
        f"Tracks compared: {summary['tracks_compared']}",
        f"Not comparable: {summary['not_comparable_tracks']}",
        f"Stable: {counts['STABLE']}",
        f"Minor: {counts['MINOR']}",
        f"Significant: {counts['SIGNIFICANT']}",
        f"Critical: {counts['CRITICAL']}",
        f"Resolved genre match: {summary['resolved_genre_match_pct']}%",
        f"Broad family match: {summary['broad_family_match_pct']}%",
        f"Tempo equivalent: {summary['tempo_equivalent_pct']}%",
        f"Key/mode match: {summary['key_mode_match_pct']}%",
    ]
    if summary.get("mode_warning"):
        lines.append(f"WARNING: {summary['mode_warning']}")
    lines.extend([f"JSON report: {json_report}", f"CSV report: {csv_report}"])
    for row in rows:
        if not row["comparable"]:
            lines.append(
                f"\n[NOT_COMPARABLE] {Path(str(row['path'])).name}: "
                f"{row['left_genre'] or row['left_quality']} -> "
                f"{row['right_genre'] or row['right_quality']} "
                f"({row['comparison_reason']})"
            )
        elif row["severity"] != "STABLE":
            lines.append(
                f"\n[{row['severity']}] {Path(str(row['path'])).name}: "
                f"{row['left_genre']} -> {row['right_genre']} ({row['reasons']})"
            )
    return "\n".join(lines)
