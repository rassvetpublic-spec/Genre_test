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
    family_ratio: float | None
    style_margin: float | None
    primary_family: str | None
    secondary_family: str | None
    secondary_style: str | None


def _split_style(label: str) -> tuple[str | None, str]:
    if "---" in label:
        family, leaf = label.split("---", 1)
        return family.strip(), leaf.strip()
    return None, label.strip()


def _human_style(label: str) -> str:
    family, leaf = _split_style(label)
    if not family:
        return leaf

    # Some Discogs labels describe form/presentation rather than a useful standalone genre.
    # Add family context only for those generic leaves; preserve specific taxonomy labels as-is.
    if leaf == "Vocal":
        return "Vocal Pop" if family == "Pop" else f"{family} Vocal"
    if leaf == "Ballad":
        return f"{family} Ballad"
    if leaf == "Acoustic":
        return f"Acoustic {family}"
    if leaf == "Parody":
        return f"{family} Parody"
    return leaf


def _style_confidence(relative_margin: float | None) -> str:
    if relative_margin is None:
        return "low-medium"
    if relative_margin >= 0.35:
        return "high"
    if relative_margin >= 0.15:
        return "medium"
    return "low-medium"


def resolve_genre(
    styles: list[StyleScore],
    broad_genres: list[StyleScore],
    hybrid_margin: float = 0.08,
    medium_margin: float = 0.20,
    hybrid_ratio: float = 0.80,
    strong_secondary_ratio: float = 0.65,
) -> GenreResolution:
    if not broad_genres:
        return GenreResolution(None, "unknown", "low", None, None, None, None, None, None)

    first = broad_genres[0]
    second = broad_genres[1] if len(broad_genres) > 1 else None
    margin = first.score - second.score if second else first.score
    family_ratio = second.score / first.score if second and first.score > 0 else None

    if second and (
        margin < hybrid_margin
        or (family_ratio is not None and family_ratio >= hybrid_ratio)
    ):
        classification = "hybrid"
        family_confidence = "low-medium"
        eligible_families = {first.label, second.label}
    elif margin < medium_margin or (
        family_ratio is not None and family_ratio >= strong_secondary_ratio
    ):
        classification = "primary"
        family_confidence = "medium"
        eligible_families = {first.label}
    else:
        classification = "primary"
        family_confidence = "high"
        eligible_families = {first.label}

    candidate = next(
        (item for item in styles if broad_genre(item.label) in eligible_families),
        None,
    )

    # Fine-style confidence must account for the strongest competing style from either of the
    # two leading broad families. This catches cases where broad-family certainty is high but
    # the exact subgenre is not, or where the best style belongs to the secondary family.
    evidence_families = {first.label}
    if second:
        evidence_families.add(second.label)
    competitor = next(
        (
            item
            for item in styles
            if broad_genre(item.label) in evidence_families
            and (candidate is None or item.label != candidate.label)
        ),
        None,
    )

    if candidate is None:
        resolved = first.label
        relative_style_margin = None
    else:
        resolved = _human_style(candidate.label)
        if competitor is None:
            relative_style_margin = 1.0
        elif candidate.score > 0:
            relative_style_margin = (candidate.score - competitor.score) / candidate.score
        else:
            relative_style_margin = None

    style_confidence = _style_confidence(relative_style_margin)

    if classification == "hybrid":
        confidence = "low-medium"
    elif family_confidence == "high":
        # A clear broad family does not justify a high-confidence subgenre when fine styles tie.
        confidence = "high" if style_confidence == "high" else "medium"
    else:
        confidence = "low-medium" if style_confidence == "low-medium" else "medium"

    return GenreResolution(
        resolved_genre=resolved,
        classification=classification,
        confidence=confidence,
        family_margin=round(margin, 6),
        family_ratio=round(family_ratio, 6) if family_ratio is not None else None,
        style_margin=(
            round(relative_style_margin, 6) if relative_style_margin is not None else None
        ),
        primary_family=first.label,
        secondary_family=second.label if second else None,
        secondary_style=_human_style(competitor.label) if competitor else None,
    )
