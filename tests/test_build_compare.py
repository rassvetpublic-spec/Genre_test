from dataclasses import replace

from genre_test.build_compare import build_coverage, compare_builds, format_build_comparison
from genre_test.build_history import BuildAwareHistoryDB
from genre_test.models import AnalysisResult, AudioFeatures, StyleScore


def _result(audio, track_id, run_id, git_commit, analyzed_at):
    return AnalysisResult(
        path=str(audio),
        primary_genre="Rock",
        primary_genre_score=0.8,
        resolved_genre="Alternative Rock",
        classification="primary",
        confidence="high",
        top_styles=[StyleScore("Rock---Alternative Rock", 0.7)],
        broad_genres=[StyleScore("Rock", 0.8)],
        audio_features=AudioFeatures(180, 16000, 120, "A", "minor", 0.1, 1000, 2000, 0.05),
        model_id="model-a",
        model_revision="revision-a",
        windows_analyzed=5,
        device="cpu",
        analysis_mode="auto",
        analyzer_version="0.4.0",
        schema_version=4,
        git_commit=git_commit,
        run_id=run_id,
        analyzed_at=analyzed_at,
        track_id=track_id,
    )


def test_build_comparison_reports_coverage_and_no_false_zero_percent_verdict(tmp_path):
    first_audio = tmp_path / "first.mp3"
    second_audio = tmp_path / "second.mp3"
    first_audio.write_bytes(b"first fake audio")
    second_audio.write_bytes(b"second fake audio")

    db = BuildAwareHistoryDB(tmp_path / "history.sqlite3")
    first_track = db.resolve_track_id(first_audio)
    second_track = db.resolve_track_id(second_audio)
    first = _result(first_audio, first_track, "run-a", "aaaaaaaa", "2026-08-25T10:00:00Z")
    second = replace(
        _result(second_audio, second_track, "run-b", "bbbbbbbb", "2026-08-25T11:00:00Z"),
        resolved_genre="Pop Rock",
    )
    db.record_result(first)
    db.record_result(second)

    builds = {build.short_commit: build for build in db.builds()}
    build_a = builds["aaaaaaaa"]
    build_b = builds["bbbbbbbb"]
    coverage = build_coverage(db, build_a, build_b, mode="auto")

    assert coverage == {
        "left_tracks": 1,
        "right_tracks": 1,
        "common_tracks": 0,
        "left_only_tracks": 1,
        "right_only_tracks": 1,
    }

    result = compare_builds(db, build_a, build_b, mode="auto", out_dir=tmp_path / "reports")
    text = format_build_comparison(*result)

    assert "Common tracks: 0" in text
    assert "no common saved tracks" in text
    assert "0.0%" not in text
    assert "will not present 0% metrics" in text
