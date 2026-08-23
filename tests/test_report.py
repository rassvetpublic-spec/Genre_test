from genre_test.models import AnalysisResult, AudioFeatures, StyleScore
from genre_test.report import write_summary_csv


def test_summary_csv(tmp_path):
    result = AnalysisResult(
        path=str(tmp_path / "a.wav"),
        primary_genre="Rock",
        primary_genre_score=0.8,
        top_styles=[StyleScore("Rock---Alternative Rock", 0.7)],
        broad_genres=[StyleScore("Rock", 0.8)],
        audio_features=AudioFeatures(10.0, 16000, 120.0, "A", "minor", 0.1, 1000, 2000, 0.05),
        model_id="test",
        model_revision=None,
        windows_analyzed=1,
        device="cpu",
    )
    path = write_summary_csv([result], tmp_path)
    text = path.read_text(encoding="utf-8-sig")
    assert "primary_genre" in text
    assert "Alternative Rock" in text
