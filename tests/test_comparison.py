from genre_test.comparison import compare_results, tempo_relation
from genre_test.models import AnalysisResult, AudioFeatures, StyleScore


def result(
    family,
    genre,
    confidence="high",
    bpm=100.0,
    key="A",
    mode="minor",
    broad=None,
    styles=None,
    classification="primary",
):
    return AnalysisResult(
        path="x.wav",
        primary_genre=family,
        primary_genre_score=0.8,
        resolved_genre=genre,
        classification=classification,
        confidence=confidence,
        top_styles=styles or [StyleScore(f"{family}---{genre}", 0.7)],
        broad_genres=broad or [StyleScore(family, 0.8), StyleScore("Pop", 0.1)],
        audio_features=AudioFeatures(
            180,
            16000,
            bpm,
            key,
            mode,
            0.1,
            1000,
            2000,
            0.05,
        ),
        model_id="m",
        model_revision=None,
        windows_analyzed=5,
        device="cpu",
    )


def test_tempo_half_double_is_equivalent():
    assert tempo_relation(81.5, 163.0) == "half-double"
    assert tempo_relation(120.0, 121.0) == "same"
    assert tempo_relation(90.0, 130.0) == "different"


def test_same_family_subgenre_change_is_minor():
    left = result("Rock", "Alternative Rock")
    right = result("Rock", "Pop Rock")
    comparison = compare_results(left, right)
    assert comparison.severity == "MINOR"
    assert comparison.broad_match
    assert not comparison.resolved_match


def test_high_confidence_family_contradiction_is_critical():
    left = result(
        "Rock",
        "Alternative Rock",
        broad=[StyleScore("Rock", 0.9)],
    )
    right = result(
        "Electronic",
        "Dance-pop",
        broad=[StyleScore("Electronic", 0.9)],
    )
    comparison = compare_results(left, right)
    assert comparison.severity == "CRITICAL"
    assert not comparison.broad_match
