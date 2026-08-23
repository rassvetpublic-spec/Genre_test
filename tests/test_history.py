from genre_test.history import HistoryDB
from genre_test.models import AnalysisResult, AudioFeatures, StyleScore


def test_history_records_and_recovers_versioned_run(tmp_path):
    audio = tmp_path / "track.mp3"
    audio.write_bytes(b"fake audio bytes")
    db = HistoryDB(tmp_path / "history.sqlite3")
    track_id = db.resolve_track_id(audio)
    result = AnalysisResult(
        path=str(audio),
        primary_genre="Rock",
        primary_genre_score=0.8,
        resolved_genre="Alternative Rock",
        classification="primary",
        confidence="high",
        top_styles=[StyleScore("Rock---Alternative Rock", 0.7)],
        broad_genres=[StyleScore("Rock", 0.8)],
        audio_features=AudioFeatures(
            180,
            16000,
            120,
            "A",
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
        analysis_mode="auto",
        analyzer_version="0.3.0",
        schema_version=2,
        run_id="run-1",
        analyzed_at="2026-08-23T17:00:00Z",
        track_id=track_id,
    )
    db.record_result(result)
    recovered = db.latest_run(
        track_id,
        mode="auto",
        analyzer_version="0.3.0",
    )
    assert recovered is not None
    assert recovered.run_id == "run-1"
    assert recovered.resolved_genre == "Alternative Rock"
    assert db.versions() == ["0.3.0"]
