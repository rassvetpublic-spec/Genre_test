from __future__ import annotations

from dataclasses import dataclass

from .aggregate import broad_genre
from .models import StyleScore


@dataclass(frozen=True)
class GenreResolution:
    resolved_genre: str | None
    classification: str
    confidence: str
    family_margin: float | None
    primary_family: str | None
    secondary_family: str | None


def _leaf_style(label: str) -> str:
    if "---" in label:
        return label.split("---", 1)[1].strip()
    return label.strip()


def resolve_genre(
    styles: list[StyleScore],
    broad_genres: list[StyleScore],
    hybrid_margin: float = 0.08,
    medium_margin: float = 0.20,
) -> GenreResolution:
    if not broad_genres:
        return GenreResolution(None, "unknown", "low", None, None, None)

    first = broad_genres[0]
    second = broad_genres[1] if len(broad_genres) > 1 else None
    margin = first.score - second.score if second else first.score

    if second and margin < hybrid_margin:
        classification = "hybrid"
        confidence = "low-medium"
        eligible_families = {first.label, second.label}
    elif margin < medium_margin:
        classification = "primary"
        confidence = "medium"
        eligible_families = {first.label}
    else:
        classification = "primary"
        confidence = "high"
        eligible_families = {first.label}

    resolved: str | None = None
    for item in styles:
        if broad_genre(item.label) in eligible_families:
            resolved = _leaf_style(item.label)
            break
    if resolved is None:
        resolved = first.label

    return GenreResolution(
        resolved_genre=resolved,
        classification=classification,
        confidence=confidence,
        family_margin=round(margin, 6),
        primary_family=first.label,
        secondary_family=second.label if second else None,
    )
