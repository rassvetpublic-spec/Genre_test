from __future__ import annotations

import json
from pathlib import Path

from genre_test.performance import (
    append_perf,
    average_seconds,
    milliseconds,
    realtime_factor,
    realtime_speed,
    tracks_per_minute,
)


def test_performance_math() -> None:
    assert milliseconds(1.23456) == 1234.56
    assert average_seconds(4, 10.0) == 2.5
    assert tracks_per_minute(4, 10.0) == 24.0
    assert realtime_factor(2.0, 100.0) == 0.02
    assert realtime_speed(2.0, 100.0) == 50.0


def test_zero_denominators_are_safe() -> None:
    assert average_seconds(0, 10.0) == 0.0
    assert tracks_per_minute(0, 10.0) == 0.0
    assert realtime_factor(1.0, 0.0) is None
    assert realtime_speed(0.0, 10.0) is None


def test_append_perf_writes_parseable_json(tmp_path: Path) -> None:
    log_path = tmp_path / "genre_test.log"
    audio_path = tmp_path / "song.wav"
    append_perf(
        "track",
        log_path=log_path,
        path=audio_path,
        elapsed_ms=123.45,
        windows=5,
    )
    line = log_path.read_text(encoding="utf-8").strip()
    payload = json.loads(line.split("PERF ", 1)[1])
    assert payload["event"] == "track"
    assert payload["elapsed_ms"] == 123.45
    assert payload["windows"] == 5
    assert payload["path"] == str(audio_path)
