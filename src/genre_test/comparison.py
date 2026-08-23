from __future__ import annotations

import math
from dataclasses import asdict, dataclass

from .models import AnalysisResult, StyleScore

SEVERITY_ORDER = {"STABLE": 0, "MINOR": 1, "SIGNIFICANT": 2, "CRITICAL": 3}


@dataclass(frozen=True)
class ComparisonResult:
    severity: str
    reasons: list[str]
    broad_match: bool
    resolved_match: bool
    classification_match: bool
    tempo_relation: str
    key_match: bool | None
    js_divergence: float
    cosine_similarity: float
    topn_weighted_overlap: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _normalized_distribution(scores: list[StyleScore]) -> dict[str, float]:
    values = {item.label: max(0.0, float(item.score)) for item in scores}
    total = sum(values.values())
    if total <= 0:
        return {}
    return {key: value / total for key, value in values.items()}


def _aligned_vectors(
    left: list[StyleScore], right: list[StyleScore]
) -> tuple[list[float], list[float]]:
    a = _normalized_distribution(left)
    b = _normalized_distribution(right)
    labels = sorted(set(a) | set(b))
    return [a.get(label, 0.0) for label in labels], [b.get(label, 0.0) for label in labels]


def cosine_similarity(left: list[StyleScore], right: list[StyleScore]) -> float:
    a, b = _aligned_vectors(left, right)
    if not a:
        return 1.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


def jensen_shannon_divergence(left: list[StyleScore], right: list[StyleScore]) -> float:
    a, b = _aligned_vectors(left, right)
    if not a:
        return 0.0
    midpoint = [(x + y) / 2.0 for x, y in zip(a, b, strict=True)]

    def kl(values: list[float], mean: list[float]) -> float:
        total = 0.0
        for value, middle in zip(values, mean, strict=True):
            if value > 0 and middle > 0:
                total += value * math.log(value / middle)
        return total

    js = 0.5 * kl(a, midpoint) + 0.5 * kl(b, midpoint)
    return max(0.0, min(1.0, js / math.log(2.0)))


def weighted_topn_overlap(
    left: list[StyleScore], right: list[StyleScore], top_n: int = 10
) -> float:
    def weights(items: list[StyleScore]) -> dict[str, float]:
        raw = {item.label: 1.0 / rank for rank, item in enumerate(items[:top_n], 1)}
        total = sum(raw.values()) or 1.0
        return {label: value / total for label, value in raw.items()}

    a = weights(left)
    b = weights(right)
    if not a and not b:
        return 1.0
    return sum(min(a.get(label, 0.0), b.get(label, 0.0)) for label in set(a) | set(b))


def tempo_relation(left_bpm: float | None, right_bpm: float | None) -> str:
    if not left_bpm or not right_bpm:
        return "unknown"

    def close(a: float, b: float) -> bool:
        return abs(a - b) <= max(1.0, 0.025 * max(a, b))

    if close(left_bpm, right_bpm):
        return "same"
    if close(left_bpm * 2.0, right_bpm) or close(left_bpm, right_bpm * 2.0):
        return "half-double"
    return "different"


def _key_match(left: AnalysisResult, right: AnalysisResult) -> bool | None:
    if not left.audio_features.key or not right.audio_features.key:
        return None
    return (
        left.audio_features.key == right.audio_features.key
        and left.audio_features.mode == right.audio_features.mode
    )


def compare_results(left: AnalysisResult, right: AnalysisResult) -> ComparisonResult:
    broad_match = left.primary_genre == right.primary_genre
    resolved_match = left.resolved_genre == right.resolved_genre
    classification_match = left.classification == right.classification
    tempo = tempo_relation(left.audio_features.bpm, right.audio_features.bpm)
    key_match = _key_match(left, right)
    js = jensen_shannon_divergence(left.broad_genres, right.broad_genres)
    cosine = cosine_similarity(left.broad_genres, right.broad_genres)
    overlap = weighted_topn_overlap(left.top_styles, right.top_styles)

    reasons: list[str] = []
    both_high = left.confidence == "high" and right.confidence == "high"

    if not broad_match and both_high:
        severity = "CRITICAL"
        reasons.append("high-confidence broad-family contradiction")
    elif js >= 0.45:
        severity = "CRITICAL"
        reasons.append("very large broad-distribution drift")
    elif not broad_match:
        severity = "SIGNIFICANT"
        reasons.append("broad family changed")
    elif not classification_match:
        severity = "SIGNIFICANT"
        reasons.append("primary/hybrid classification changed")
    elif js >= 0.20:
        severity = "SIGNIFICANT"
        reasons.append("large broad-distribution drift")
    elif tempo == "different":
        severity = "SIGNIFICANT"
        reasons.append("tempo is not equivalent, half-time or double-time")
    elif not resolved_match:
        severity = "MINOR"
        reasons.append("resolved fine style changed within the same broad family")
    elif js >= 0.08:
        severity = "MINOR"
        reasons.append("moderate broad-distribution drift")
    elif key_match is False:
        severity = "MINOR"
        reasons.append("key/mode changed")
    elif overlap < 0.50:
        severity = "MINOR"
        reasons.append("detailed Top-N style overlap is low")
    else:
        severity = "STABLE"
        reasons.append("genre evidence is convergent")

    return ComparisonResult(
        severity=severity,
        reasons=reasons,
        broad_match=broad_match,
        resolved_match=resolved_match,
        classification_match=classification_match,
        tempo_relation=tempo,
        key_match=key_match,
        js_divergence=round(js, 6),
        cosine_similarity=round(cosine, 6),
        topn_weighted_overlap=round(overlap, 6),
    )
