from __future__ import annotations

import csv
import json
import uuid
from pathlib import Path

from .models import AnalysisResult


def _safe_token(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in value)


def write_json(result: AnalysisResult, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    run_token = (result.run_id or str(uuid.uuid4())).replace("-", "")[:8]
    version = _safe_token(result.analyzer_version or "unknown")
    mode = _safe_token(result.analysis_mode or "unknown")
    target = out_dir / f"{result.stem}.genre.{version}.{mode}.{run_token}.json"
    target.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def write_summary_csv(results: list[AnalysisResult], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "summary.csv"
    fields = [
        "track_id",
        "run_id",
        "analyzed_at",
        "analyzer_version",
        "schema_version",
        "path",
        "input_quality",
        "quality_notes",
        "resolved_genre",
        "classification",
        "confidence",
        "primary_genre",
        "primary_genre_score",
        "secondary_genre",
        "secondary_style",
        "family_margin",
        "family_ratio",
        "style_margin",
        "analysis_mode",
        "windows_analyzed",
        "window_seconds",
        "internal_top_k",
        "report_top_k",
        "bpm",
        "key",
        "mode",
        "top_style_1",
        "top_style_1_score",
        "top_style_2",
        "top_style_2_score",
        "top_style_3",
        "top_style_3_score",
        "device",
        "model_id",
        "model_revision",
        "git_commit",
    ]
    with target.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for result in results:
            styles = result.top_styles[:3]
            row = {
                "track_id": result.track_id,
                "run_id": result.run_id,
                "analyzed_at": result.analyzed_at,
                "analyzer_version": result.analyzer_version,
                "schema_version": result.schema_version,
                "path": result.path,
                "input_quality": result.input_quality,
                "quality_notes": "; ".join(result.quality_notes),
                "resolved_genre": result.resolved_genre,
                "classification": result.classification,
                "confidence": result.confidence,
                "primary_genre": result.primary_genre,
                "primary_genre_score": result.primary_genre_score,
                "secondary_genre": result.secondary_genre,
                "secondary_style": result.secondary_style,
                "family_margin": result.family_margin,
                "family_ratio": result.family_ratio,
                "style_margin": result.style_margin,
                "analysis_mode": result.analysis_mode,
                "windows_analyzed": result.windows_analyzed,
                "window_seconds": result.window_seconds,
                "internal_top_k": result.internal_top_k,
                "report_top_k": result.report_top_k,
                "bpm": result.audio_features.bpm,
                "key": result.audio_features.key,
                "mode": result.audio_features.mode,
                "device": result.device,
                "model_id": result.model_id,
                "model_revision": result.model_revision,
                "git_commit": result.git_commit,
            }
            for i in range(3):
                row[f"top_style_{i+1}"] = styles[i].label if i < len(styles) else ""
                row[f"top_style_{i+1}_score"] = round(styles[i].score, 6) if i < len(styles) else ""
            writer.writerow(row)
    return target


def write_validation_report(
    summary: dict[str, object], rows: list[dict[str, object]], out_dir: Path
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    session_id = str(summary.get("session_id") or uuid.uuid4())
    token = session_id.replace("-", "")[:8]
    json_path = out_dir / f"validation.{token}.json"
    csv_path = out_dir / f"validation.{token}.csv"
    json_path.write_text(
        json.dumps({"summary": summary, "tracks": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    fieldnames = [
        "track_id",
        "path",
        "status",
        "severity",
        "mode_severity",
        "mode_worst_pair",
        "mode_reasons",
        "history_severity",
        "history_worst_mode",
        "history_reasons",
        "modes",
        "convergence",
        "resolved_genres",
        "versions",
        "input_quality",
        "fast_windows",
        "auto_windows",
        "accurate_windows",
        "auto_saved_windows_pct",
        "notes",
    ]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
    return json_path, csv_path


def write_version_comparison_report(
    summary: dict[str, object], rows: list[dict[str, object]], out_dir: Path
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    left = _safe_token(str(summary.get("version_a", "left")))
    right = _safe_token(str(summary.get("version_b", "right")))
    mode = _safe_token(str(summary.get("mode", "all")))
    json_path = out_dir / f"version_compare.{left}_vs_{right}.{mode}.json"
    csv_path = out_dir / f"version_compare.{left}_vs_{right}.{mode}.csv"
    json_path.write_text(
        json.dumps({"summary": summary, "tracks": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    fieldnames = [
        "track_id",
        "path",
        "severity",
        "left_genre",
        "right_genre",
        "left_family",
        "right_family",
        "tempo_relation",
        "js_divergence",
        "cosine_similarity",
        "topn_weighted_overlap",
        "reasons",
    ]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
    return json_path, csv_path
