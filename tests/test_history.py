import sqlite3
from dataclasses import replace

from genre_test.comparison import compare_results
from genre_test.history import HistoryDB
from genre_test.models import AnalysisResult, AudioFeatures, StyleScore
from genre_test.track_identity import identify_track


def make_result(audio, track_id, run_id="run-1", version="0.3.0"):
    return AnalysisResult(
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
        analyzer_version=version,
        schema_version=2,
        run_id=run_id,
        analyzed_at="2026-08-23T17:00:00Z",
        track_id=track_id,
    )


def test_history_records_and_recovers_versioned_run(tmp_path):
    audio = tmp_path / "track.mp3"
    audio.write_bytes(b"fake audio bytes")
    db = HistoryDB(tmp_path / "history.sqlite3")
    track_id = db.resolve_track_id(audio)
    result = make_result(audio, track_id)
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


def test_record_result_registers_file_location_even_with_precomputed_track_id(tmp_path):
    audio = tmp_path / "track.mp3"
    audio.write_bytes(b"fake audio bytes")
    db = HistoryDB(tmp_path / "history.sqlite3")
    track_id = identify_track(audio).track_id
    db.record_result(make_result(audio, track_id))

    with sqlite3.connect(db.path) as conn:
        row = conn.execute(
            "SELECT track_id FROM file_locations WHERE path = ?",
            (str(audio.resolve()),),
        ).fetchone()
    assert row is not None
    assert row[0] == track_id


def test_re_recording_same_run_does_not_delete_existing_comparison(tmp_path):
    audio = tmp_path / "track.mp3"
    audio.write_bytes(b"fake audio bytes")
    db = HistoryDB(tmp_path / "history.sqlite3")
    track_id = db.resolve_track_id(audio)
    left = make_result(audio, track_id, run_id="run-1", version="0.2.1")
    right = replace(
        make_result(audio, track_id, run_id="run-2", version="0.3.0"),
        resolved_genre="Pop Rock",
        top_styles=[StyleScore("Rock---Pop Rock", 0.7)],
        analyzed_at="2026-08-23T18:00:00Z",
    )
    db.record_result(left)
    db.record_result(right)
    comparison = compare_results(left, right)
    db.store_comparison(track_id, "run-1", "run-2", comparison, "version")
    assert db.latest_severity(track_id) == "MINOR"

    db.record_result(left)
    assert db.latest_severity(track_id) == "MINOR"
