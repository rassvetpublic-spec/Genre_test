from __future__ import annotations

from collections import defaultdict

from .models import AnalysisResult, AudioProfile, SemanticEvidence, StyleScore

AST_FAMILY_MAP = {
    "pop music": "Pop",
    "vocal music": "Pop",
    "hip hop music": "Hip Hop",
    "rock music": "Rock",
    "heavy metal": "Rock",
    "punk rock": "Rock",
    "grunge": "Rock",
    "progressive rock": "Rock",
    "rock and roll": "Rock",
    "psychedelic rock": "Rock",
    "electronic music": "Electronic",
    "house music": "Electronic",
    "techno": "Electronic",
    "dubstep": "Electronic",
    "drum and bass": "Electronic",
    "electronica": "Electronic",
    "electronic dance music": "Electronic",
    "ambient music": "Electronic",
    "trance music": "Electronic",
    "rhythm and blues": "Funk / Soul",
    "soul music": "Funk / Soul",
    "funk": "Funk / Soul",
    "jazz": "Jazz",
    "classical music": "Classical",
    "opera": "Classical",
    "reggae": "Reggae",
    "country": "Folk, World, & Country",
    "folk music": "Folk, World, & Country",
    "bluegrass": "Folk, World, & Country",
    "middle eastern music": "Folk, World, & Country",
    "music of latin america": "Latin",
    "salsa music": "Latin",
    "flamenco": "Latin",
    "blues": "Blues",
}

DISTRIBUTOR_FAMILY_MAP = {
    "Pop": "Pop",
    "Rock": "Rock",
    "Electronic": "Electronic",
    "Hip Hop": "Hip-Hop/Rap",
    "Funk / Soul": "R&B/Soul",
    "Folk, World, & Country": "Folk/World/Country",
    "Stage & Screen": "Soundtrack",
    "Classical": "Classical",
    "Jazz": "Jazz",
    "Latin": "Latin",
    "Reggae": "Reggae",
    "Blues": "Blues",
}

SPECIFIC_VOCALS = {
    "male singing",
    "female singing",
    "child singing",
    "synthetic singing",
    "choir",
    "chant",
    "mantra",
    "rapping",
    "humming",
    "a capella",
}


def _clean_style(label: str) -> str:
    return label.split("---", 1)[-1].strip()


def _style_family(label: str) -> str | None:
    if "---" not in label:
        return None
    return label.split("---", 1)[0].strip()


def _style_matches_resolved(item: StyleScore, resolved_style: str) -> bool:
    family = _style_family(item.label)
    clean = _clean_style(item.label)
    expected = resolved_style.casefold().strip()
    aliases = {clean.casefold()}
    if family:
        aliases.add(f"{family} {clean}".casefold())
        aliases.add(f"{clean} {family}".casefold())
    return expected in aliases


def _resolved_style_family(items: list[StyleScore], resolved_style: str | None) -> str | None:
    if not resolved_style:
        return None
    match = next((item for item in items if _style_matches_resolved(item, resolved_style)), None)
    return _style_family(match.label) if match is not None else None


def _best_style_for_family(items: list[StyleScore], family: str | None) -> StyleScore | None:
    if not family:
        return None
    return next((item for item in items if _style_family(item.label) == family), None)


def _normalize_scores(items: list[StyleScore]) -> dict[str, float]:
    total = sum(max(0.0, item.score) for item in items)
    if total <= 0.0:
        return {}
    return {item.label: max(0.0, item.score) / total for item in items}


def _semantic_family_totals(evidence: SemanticEvidence | None) -> dict[str, float]:
    if evidence is None or evidence.status != "ok":
        return {}
    totals: dict[str, float] = defaultdict(float)
    for item in evidence.genre_tags:
        family = AST_FAMILY_MAP.get(item.label.casefold())
        if family:
            totals[family] += max(0.0, item.score)
    return dict(totals)


def semantic_family_scores(evidence: SemanticEvidence | None) -> list[StyleScore]:
    totals = _semantic_family_totals(evidence)
    total = sum(totals.values())
    if total <= 0.0:
        return []
    return [
        StyleScore(label, round(score / total, 6))
        for label, score in sorted(totals.items(), key=lambda pair: pair[1], reverse=True)
    ]


def fuse_family_evidence(
    maest: list[StyleScore],
    semantic: SemanticEvidence | None,
    *,
    maest_weight: float = 0.75,
) -> tuple[list[StyleScore], str]:
    maest_norm = _normalize_scores(maest)
    ast_totals = _semantic_family_totals(semantic)
    ast_total = sum(ast_totals.values())
    ast_items = semantic_family_scores(semantic)
    ast_norm = {item.label: item.score for item in ast_items}
    if not ast_norm or ast_total <= 0.0:
        return [StyleScore(label, round(score, 6)) for label, score in maest_norm.items()], "maest_only"

    # AudioSet class probabilities are absolute evidence, not a categorical
    # distribution. Preserve that strength before normalizing across mapped
    # families so a lone weak tag (for example Rock=0.03) cannot receive the
    # full semantic vote merely because it is the only recognized family.
    ast_strength = min(1.0, ast_total)
    max_ast_weight = 1.0 - maest_weight
    ast_weight = max_ast_weight * ast_strength
    effective_maest_weight = 1.0 - ast_weight

    labels = set(maest_norm) | set(ast_norm)
    combined = {
        label: effective_maest_weight * maest_norm.get(label, 0.0) + ast_weight * ast_norm.get(label, 0.0)
        for label in labels
    }
    evidence = [
        StyleScore(label, round(score, 6))
        for label, score in sorted(combined.items(), key=lambda pair: pair[1], reverse=True)
    ]
    maest_top = maest[0].label if maest else None
    ast_top = ast_items[0].label if ast_items else None
    agreement = "agree" if maest_top and maest_top == ast_top else "mixed"
    return evidence, agreement


def _profile_confidence(raw: str, agreement: str) -> str:
    if agreement != "mixed":
        return raw
    if raw == "high":
        return "medium"
    if raw == "medium":
        return "low-medium"
    return raw


def _vocal_summary(evidence: SemanticEvidence | None) -> str | None:
    if evidence is None:
        return None
    specific = [item for item in evidence.vocal_tags if item.label.casefold() in SPECIFIC_VOCALS]
    if specific:
        return specific[0].label
    return evidence.vocal_tags[0].label if evidence.vocal_tags else None


def _unique_labels(items: list[StyleScore], *, limit: int, skip: set[str] | None = None) -> tuple[str, ...]:
    blocked = {item.casefold() for item in (skip or set())}
    output: list[str] = []
    seen: set[str] = set()
    for item in items:
        label = item.label.strip()
        key = label.casefold()
        if key in blocked or key in seen:
            continue
        seen.add(key)
        output.append(label)
        if len(output) >= limit:
            break
    return tuple(output)


def _suno_style(
    primary: str | None,
    secondary: str | None,
    moods: tuple[str, ...],
    vocal: str | None,
    instruments: tuple[str, ...],
    result: AnalysisResult,
) -> str | None:
    if primary is None:
        return None
    parts: list[str] = [primary]
    if secondary and secondary.casefold() != primary.casefold():
        parts.append(f"{secondary} influence")
    parts.extend(moods[:2])
    if vocal:
        parts.append(vocal)
    parts.extend(instruments[:3])
    if result.audio_features.bpm:
        parts.append(f"{result.audio_features.bpm:.0f} BPM")
    if result.audio_features.key:
        key = result.audio_features.key
        if result.audio_features.mode:
            key += f" {result.audio_features.mode}"
        parts.append(key)
    return ", ".join(parts)


def build_audio_profile(
    result: AnalysisResult,
    semantic: SemanticEvidence | None = None,
) -> AudioProfile:
    family_evidence, agreement = fuse_family_evidence(result.broad_genres, semantic)
    maest_family = result.primary_genre
    final_family = maest_family
    if family_evidence and result.confidence != "high":
        final_family = family_evidence[0].label

    original_primary_style = result.resolved_genre
    primary_style = original_primary_style
    resolved_family = _resolved_style_family(result.top_styles, primary_style)

    if final_family and resolved_family and final_family != resolved_family:
        candidate = _best_style_for_family(result.top_styles, final_family)
        if candidate is not None:
            primary_style = _clean_style(candidate.label)
        else:
            # Never publish a family that contradicts a resolved style when no
            # same-family candidate exists in the MAEST evidence.
            final_family = resolved_family
    elif final_family and final_family != maest_family:
        candidate = _best_style_for_family(result.top_styles, final_family)
        if candidate is not None:
            primary_style = _clean_style(candidate.label)

    if primary_style != original_primary_style and original_primary_style:
        secondary = original_primary_style
    elif final_family != maest_family and result.resolved_genre:
        secondary = result.resolved_genre
    else:
        secondary = result.secondary_style or result.secondary_genre

    adjacent: list[str] = []
    blocked = {value.casefold() for value in (primary_style, secondary) if value}
    for item in result.top_styles:
        label = _clean_style(item.label)
        if label.casefold() in blocked or label in adjacent:
            continue
        adjacent.append(label)
        if len(adjacent) >= 4:
            break

    moods = _unique_labels(semantic.mood_tags if semantic else [], limit=3)
    vocal = _vocal_summary(semantic)
    instruments = _unique_labels(
        semantic.instrument_tags if semantic else [],
        limit=4,
        skip={"Musical instrument"},
    )
    production = _unique_labels(semantic.production_tags if semantic else [], limit=3)

    distributor_genre = DISTRIBUTOR_FAMILY_MAP.get(final_family or "", final_family)
    distributor_subgenre = primary_style if primary_style and primary_style != final_family else None
    sources = ("maest", "audioset_ast") if semantic and semantic.status == "ok" else ("maest",)
    semantic_status = semantic.status if semantic is not None else "not_available"

    return AudioProfile(
        primary_genre=primary_style,
        broad_family=final_family,
        confidence=_profile_confidence(result.confidence, agreement),
        secondary_influence=secondary,
        adjacent_genres=tuple(adjacent),
        moods=moods,
        vocal=vocal,
        instruments=instruments,
        production=production,
        distributor_genre=distributor_genre,
        distributor_subgenre=distributor_subgenre,
        suno_style=_suno_style(primary_style, secondary, moods, vocal, instruments, result),
        ensemble_agreement=agreement,
        ensemble_sources=sources,
        family_evidence=family_evidence,
        semantic_status=semantic_status,
    )
