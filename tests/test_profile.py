from __future__ import annotations

from dataclasses import replace

from genre_test import __version__

from genre_test.models import (
    AnalysisResult,
    AudioFeatures,
    SemanticEvidence,
    StyleScore,
)
from genre_test.presentation import format_result_text
from genre_test.profile import build_audio_profile, fuse_family_evidence, semantic_family_scores
from genre_test.semantic import group_semantic_tags


def _base_result(confidence: str = "low-medium") -> AnalysisResult:
    return AnalysisResult(
        path="C:/Music/test.wav",
        primary_genre="Pop",
        primary_genre_score=0.402,
        top_styles=[
            StyleScore("Rock---Pop Rock", 0.1985),
            StyleScore("Pop---Ballad", 0.1294),
            StyleScore("Pop---Europop", 0.1076),
        ],
        broad_genres=[
            StyleScore("Pop", 0.4020),
            StyleScore("Rock", 0.3114),
        ],
        audio_features=AudioFeatures(
            duration_s=180.0,
            sample_rate=16000,
            bpm=81.52,
            key="C",
            mode="minor",
            rms=0.1,
            spectral_centroid_hz=1000.0,
            spectral_rolloff_hz=2000.0,
            zero_crossing_rate=0.05,
        ),
        model_id="maest/model",
        model_revision="maest-rev",
        windows_analyzed=5,
        device="cuda",
        resolved_genre="Pop Ballad",
        classification="hybrid",
        confidence=confidence,
        secondary_genre="Rock",
        secondary_style="Pop Rock",
        analysis_mode="auto",
        schema_version=4,
        analyzer_version=__version__,
    )


def _semantic() -> SemanticEvidence:
    tags = [
        StyleScore("Rock music", 0.80),
        StyleScore("Male singing", 0.72),
        StyleScore("Electric guitar", 0.61),
        StyleScore("Drum kit", 0.59),
        StyleScore("Exciting music", 0.44),
        StyleScore("Electronic music", 0.10),
    ]
    groups = group_semantic_tags(tags)
    return SemanticEvidence(
        model_id="MIT/ast",
        model_revision="ast-rev",
        device="cuda",
        windows_analyzed=3,
        top_tags=tags,
        genre_tags=groups["genre"],
        mood_tags=groups["mood"],
        vocal_tags=groups["vocal"],
        instrument_tags=groups["instrument"],
        production_tags=groups["production"],
    )


def test_semantic_groups_music_specific_tags() -> None:
    semantic = _semantic()
    assert semantic.genre_tags[0].label == "Rock music"
    assert semantic.vocal_tags[0].label == "Male singing"
    assert {item.label for item in semantic.instrument_tags} == {"Electric guitar", "Drum kit"}
    assert semantic.mood_tags[0].label == "Exciting music"


def test_semantic_family_mapping_normalizes_audioset_evidence() -> None:
    families = semantic_family_scores(_semantic())
    assert families[0].label == "Rock"
    assert abs(sum(item.score for item in families) - 1.0) < 1e-5


def test_weak_absolute_ast_evidence_cannot_override_maest_family() -> None:
    maest = [
        StyleScore("Pop", 0.40),
        StyleScore("Rock", 0.35),
        StyleScore("Electronic", 0.25),
    ]
    weak_semantic = replace(_semantic(), genre_tags=[StyleScore("Rock music", 0.03)])

    evidence, agreement = fuse_family_evidence(maest, weak_semantic)

    assert agreement == "mixed"
    assert evidence[0].label == "Pop"
    scores = {item.label: item.score for item in evidence}
    assert scores["Pop"] > scores["Rock"]


def test_fusion_can_switch_low_confidence_family_with_independent_evidence() -> None:
    result = _base_result()
    evidence, agreement = fuse_family_evidence(result.broad_genres, _semantic())
    assert agreement == "mixed"
    assert evidence[0].label == "Rock"

    profile = build_audio_profile(result, _semantic())
    assert profile.broad_family == "Rock"
    assert profile.primary_genre == "Pop Rock"
    assert profile.secondary_influence == "Pop Ballad"
    assert profile.vocal == "Male singing"
    assert "Electric guitar" in profile.instruments
    assert profile.ensemble_sources == ("maest", "audioset_ast")


def test_profile_reconciles_resolved_style_with_selected_family() -> None:
    result = replace(
        _base_result(),
        primary_genre="Electronic",
        primary_genre_score=0.4685,
        broad_genres=[
            StyleScore("Electronic", 0.4685),
            StyleScore("Pop", 0.2708),
            StyleScore("Rock", 0.1427),
        ],
        top_styles=[
            StyleScore("Pop---Indie Pop", 0.1278),
            StyleScore("Electronic---Synth-pop", 0.1272),
            StyleScore("Rock---Pop Rock", 0.0916),
        ],
        resolved_genre="Indie Pop",
        secondary_genre="Pop",
        secondary_style="Synth-pop",
    )

    profile = build_audio_profile(result)

    assert profile.broad_family == "Electronic"
    assert profile.primary_genre == "Synth-pop"
    assert profile.secondary_influence == "Indie Pop"
    assert profile.distributor_genre == "Electronic"
    assert profile.distributor_subgenre == "Synth-pop"


def test_profile_falls_back_to_resolved_family_when_selected_family_has_no_style() -> None:
    result = replace(
        _base_result(),
        primary_genre="Electronic",
        primary_genre_score=0.60,
        broad_genres=[StyleScore("Electronic", 0.60), StyleScore("Pop", 0.30)],
        top_styles=[StyleScore("Pop---Indie Pop", 0.20)],
        resolved_genre="Indie Pop",
    )

    profile = build_audio_profile(result)

    assert profile.primary_genre == "Indie Pop"
    assert profile.broad_family == "Pop"
    assert profile.distributor_genre == "Pop"


def test_high_confidence_maest_family_is_not_overridden() -> None:
    result = _base_result(confidence="high")
    profile = build_audio_profile(result, _semantic())
    assert profile.broad_family == "Pop"
    assert profile.primary_genre == "Pop Ballad"
    assert profile.confidence == "medium"


def test_profile_round_trip_and_product_views() -> None:
    result = _base_result()
    semantic = _semantic()
    profile = build_audio_profile(result, semantic)
    enriched = AnalysisResult.from_dict(
        {
            **result.to_dict(),
            "semantic_evidence": semantic.__dict__,
            "audio_profile": profile.__dict__,
        }
    )
    assert enriched.audio_profile is not None
    assert enriched.semantic_evidence is not None
    normal = format_result_text(enriched, view="normal")
    suno = format_result_text(enriched, view="suno")
    distributor = format_result_text(enriched, view="distributor")
    combined = format_result_text(enriched)
    combined_with_path = format_result_text(enriched, include_path=True)
    assert "Genre: Pop Rock" in normal
    assert "Vocal: Male singing" in normal
    assert "SUNO Style of Music:" in suno
    assert "Distributor genre:" in distributor
    assert "[ОБЫЧНЫЙ]" in combined
    assert "[SUNO]" in combined
    assert "[ДИСТРИБЬЮТОР]" in combined
    assert "Genre: Pop Rock" in combined
    assert "SUNO Style of Music:" in combined
    assert "Distributor genre:" in combined
    assert "Full path: C:/Music/test.wav" not in combined
    assert "Full path: C:/Music/test.wav" in combined_with_path
    assert "Run ID:" not in normal
    assert "MAEST revision:" not in normal
