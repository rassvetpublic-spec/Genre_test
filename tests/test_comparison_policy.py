from genre_test.comparison_policy import version_comparability
from genre_test.models import AnalysisResult, AudioFeatures, StyleScore


def result(genre: str | None, quality: str = "NORMAL") -> AnalysisResult:
    return AnalysisResult(
        path="x.wav",
        primary_genre="Rock" if genre else None,
        primary_genre_score=0.8 if genre else None,
        resolved_genre=genre,
        classification="primary" if genre else "insufficient_audio",
        confidence="high" if genre else "low",
        top_styles=[StyleScore("Rock---Pop Rock", 0.7)] if genre else [],
        broad_genres=[StyleScore("Rock", 0.8)] if genre else [],
        audio_features=AudioFeatures(180, 16000, 120.0, "A", "minor", 0.1, 1000, 2000, 0.05),
        model_id="m",
        model_revision="rev",
        windows_analyzed=5 if genre else 0,
        device="cpu",
        input_quality=quality,
    )


def test_insufficient_audio_is_not_comparable() -> None:
    comparable, reason = version_comparability(
        result("House"),
        result(None, "INSUFFICIENT_AUDIO"),
    )
    assert comparable is False
    assert "insufficient" in reason


def test_normal_genre_verdicts_are_comparable() -> None:
    comparable, reason = version_comparability(result("Pop Rock"), result("Alternative Rock"))
    assert comparable is True
    assert reason == ""
