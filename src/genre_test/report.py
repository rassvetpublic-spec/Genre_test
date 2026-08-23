from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import AnalysisResult


def write_json(result: AnalysisResult, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{result.stem}.genre.json"
    target.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def write_summary_csv(results: list[AnalysisResult], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "summary.csv"
    fields = [
        "path",
        "primary_genre",
        "primary_genre_score",
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
    ]
    with target.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for result in results:
            styles = result.top_styles[:3]
            row = {
                "path": result.path,
                "primary_genre": result.primary_genre,
                "primary_genre_score": result.primary_genre_score,
                "bpm": result.audio_features.bpm,
                "key": result.audio_features.key,
                "mode": result.audio_features.mode,
                "device": result.device,
                "model_id": result.model_id,
            }
            for i in range(3):
                row[f"top_style_{i+1}"] = styles[i].label if i < len(styles) else ""
                row[f"top_style_{i+1}_score"] = round(styles[i].score, 6) if i < len(styles) else ""
            writer.writerow(row)
    return target
