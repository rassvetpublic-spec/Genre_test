from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .models import StyleScore


def normalize_label(label: str) -> str:
    return " ".join(label.strip().split())


def broad_genre(label: str) -> str:
    label = normalize_label(label)
    if "---" in label:
        return label.split("---", 1)[0].strip()
    if " / " in label:
        return label.split(" / ", 1)[0].strip()
    return label


def aggregate_predictions(
    predictions: Iterable[Iterable[dict[str, float | str]]],
    top_k: int = 15,
) -> tuple[list[StyleScore], list[StyleScore]]:
    windows = list(predictions)
    if not windows:
        return [], []

    style_sum: dict[str, float] = defaultdict(float)
    genre_sum: dict[str, float] = defaultdict(float)

    for window in windows:
        seen_styles: set[str] = set()
        for item in window:
            label = normalize_label(str(item["label"]))
            score = max(0.0, float(item["score"]))
            # One contribution per label per window protects against malformed duplicate rows.
            if label in seen_styles:
                continue
            seen_styles.add(label)
            style_sum[label] += score
            genre_sum[broad_genre(label)] += score

    denom = float(len(windows))
    styles = [StyleScore(k, v / denom) for k, v in style_sum.items()]
    genres = [StyleScore(k, v / denom) for k, v in genre_sum.items()]
    styles.sort(key=lambda x: x.score, reverse=True)
    genres.sort(key=lambda x: x.score, reverse=True)
    return styles[:top_k], genres[:top_k]
