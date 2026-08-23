from genre_test.models import AnalysisResult, AudioFeatures, StyleScore
from genre_test.presentation import format_result_text, tempo_candidates


def _result() -> AnalysisResult:
    return AnalysisResult(
        path="C:/Music/test.wav",
        primary_genre="Pop",
        primary_genre_score=0.402,
        top_styles=[
            StyleScore("Rock---Pop Rock", 0.1985),
            StyleScore("Pop---Ballad", 0.1294),
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
        model_revision="deadbeef",
        windows_analyzed=7,
        device="cuda",
        resolved_genre="Pop Rock",
        classification="hybrid",
        confidence="low-medium",
        secondary_genre="Rock",
        secondary_style="Pop Ballad",
        analysis_mode="auto",
        schema_version=3,
        analyzer_version="0.3.6",
        run_id="run-secret-hash",
        track_id="sha256:track-secret-hash",
    )


def test_tempo_candidates():
    value = tempo_candidates(81.52)
    assert "81.52 BPM" in value
    assert "40.76" in value
    assert "163.04" in value


def test_normal_result_is_compact_and_uses_combined_score_table():
    text = format_result_text(_result())
    assert "Genre: Pop Rock" in text
    assert "Top style" in text
    assert "Broad family" in text
    assert "Rock---Pop Rock" in text
    assert "Pop" in text
    assert "Run ID:" not in text
    assert "Track ID:" not in text
    assert "MAEST model:" not in text
    assert "MAEST revision:" not in text
    assert "Analyzer version:" not in text


def test_detailed_result_keeps_internal_metadata_for_diagnostics():
    text = format_result_text(_result(), detailed=True)
    assert "Run ID: run-secret-hash" in text
    assert "Track ID: sha256:track-secret-hash" in text
    assert "MAEST model: maest/model" in text
    assert "MAEST revision: deadbeef" in text
    assert "Analyzer version: 0.3.6" in text
