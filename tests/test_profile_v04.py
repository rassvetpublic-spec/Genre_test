from __future__ import annotations

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
        analyzer_version="0.4.0",
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
    assert "Genre: Pop Rock" in normal
    assert "Vocal: Male singing" in normal
    assert "SUNO Style of Music:" in suno
    assert "Distributor genre:" in distributor
    assert "Run ID:" not in normal
    assert "MAEST revision:" not in normal
