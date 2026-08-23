from genre_test.convergence import compare_modes
from genre_test.models import AnalysisResult, AudioFeatures, StyleScore


def make(mode, genre="Dance-pop"):
    return AnalysisResult(
        path="x.wav",
        primary_genre="Electronic",
        primary_genre_score=0.7,
        resolved_genre=genre,
        classification="primary",
        confidence="high",
        top_styles=[StyleScore(f"Electronic---{genre}", 0.7)],
        broad_genres=[StyleScore("Electronic", 0.8), StyleScore("Pop", 0.1)],
        audio_features=AudioFeatures(
            200,
            16000,
            120,
            "C",
            "minor",
            0.1,
            1000,
            2000,
            0.05,
        ),
        model_id="m",
        model_revision=None,
        windows_analyzed=5,
        device="cpu",
        analysis_mode=mode,
    )


def test_convergence_high_when_modes_agree():
    result = compare_modes(
        {
            "fast": make("fast"),
            "auto": make("auto"),
            "accurate": make("accurate"),
        }
    )
    assert result.level == "HIGH"
    assert result.worst_severity == "STABLE"
