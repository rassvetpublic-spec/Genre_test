from __future__ import annotations

import csv
import json
from pathlib import Path

from .service import SearchResult


def write_search_json(result: SearchResult, path: Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target


def write_search_csv(result: SearchResult, path: Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "rank",
        "track_id",
        "path",
        "similarity",
        "family",
        "genre",
        "confidence",
        "bpm",
        "key",
        "vocal",
        "moods",
        "instruments",
        "production",
        "backend_fingerprint",
    ]
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for hit in result.hits:
            writer.writerow(
                {
                    "rank": hit.rank,
                    "track_id": hit.track_id,
                    "path": hit.path,
                    "similarity": f"{hit.similarity:.9f}",
                    "family": hit.family or "",
                    "genre": hit.genre or "",
                    "confidence": hit.confidence or "",
                    "bpm": "" if hit.bpm is None else f"{hit.bpm:.6g}",
                    "key": hit.key or "",
                    "vocal": hit.vocal or "",
                    "moods": " | ".join(hit.moods),
                    "instruments": " | ".join(hit.instruments),
                    "production": " | ".join(hit.production),
                    "backend_fingerprint": hit.backend_fingerprint,
                }
            )
    return target
