from dataclasses import replace

from genre_test.build_history import (
    BuildAwareHistoryDB,
    current_build,
    should_recheck_build,
)
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


def test_same_semver_different_commits_are_distinct_builds(tmp_path):
    audio = tmp_path / "track.mp3"
    audio.write_bytes(b"fake audio bytes")
    db = BuildAwareHistoryDB(tmp_path / "history.sqlite3")
    track_id = db.resolve_track_id(audio)
    first = _result(audio, track_id, "run-1", "aaaaaaaa11111111", "2026-08-25T10:00:00Z")
    second = replace(
        first,
        run_id="run-2",
        git_commit="bbbbbbbb22222222",
        analyzed_at="2026-08-25T11:00:00Z",
    )
    db.record_result(first)
    db.record_result(second)

    builds = db.builds()
    assert len(builds) == 2
    assert builds[0].key != builds[1].key
    assert builds[0].analyzer_version == builds[1].analyzer_version == "0.4.0"
    assert "aaaaaaaa" in builds[0].label
    assert "bbbbbbbb" in builds[1].label


def test_latest_run_info_exposes_build_key_for_validation(tmp_path):
    audio = tmp_path / "track.mp3"
    audio.write_bytes(b"fake audio bytes")
    db = BuildAwareHistoryDB(tmp_path / "history.sqlite3")
    track_id = db.resolve_track_id(audio)
    result = _result(audio, track_id, "run-1", "aaaaaaaa11111111", "2026-08-25T10:00:00Z")
    db.record_result(result)

    info = db.latest_run_info(track_id, "auto")
    build = db.builds()[0]
    assert info is not None
    assert info.analyzer_version == build.key


def test_repeatability_query_returns_two_latest_runs(tmp_path):
    audio = tmp_path / "track.mp3"
    audio.write_bytes(b"fake audio bytes")
    db = BuildAwareHistoryDB(tmp_path / "history.sqlite3")
    track_id = db.resolve_track_id(audio)
    base = _result(audio, track_id, "run-1", "aaaaaaaa11111111", "2026-08-25T10:00:00Z")
    db.record_result(base)
    db.record_result(replace(base, run_id="run-2", analyzed_at="2026-08-25T11:00:00Z"))
    db.record_result(replace(base, run_id="run-3", analyzed_at="2026-08-25T12:00:00Z"))

    build = db.builds()[0]
    runs = db.runs_for_build(track_id, build, "auto", limit=2)
    assert [run.run_id for run in runs] == ["run-3", "run-2"]


def test_old_build_filter_uses_current_build_identity():
    current_key = current_build().key
    assert not should_recheck_build(
        "old_versions",
        "ignored-semver",
        current_key,
        "high",
        "primary",
        "STABLE",
    )
    assert should_recheck_build(
        "old_versions",
        "ignored-semver",
        current_key + "-different",
        "high",
        "primary",
        "STABLE",
    )
