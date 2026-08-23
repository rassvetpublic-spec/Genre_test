from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any

from .logging_utils import append_log


def clock() -> float:
    """Return a monotonic high-resolution timestamp for elapsed-time measurements."""
    return perf_counter()


def elapsed_seconds(start: float) -> float:
    return max(0.0, perf_counter() - start)


def milliseconds(seconds: float) -> float:
    return round(max(0.0, seconds) * 1000.0, 2)


def tracks_per_minute(count: int, seconds: float) -> float:
    if count <= 0 or seconds <= 0:
        return 0.0
    return round(60.0 * count / seconds, 3)


def average_seconds(count: int, seconds: float) -> float:
    if count <= 0 or seconds <= 0:
        return 0.0
    return round(seconds / count, 3)


def realtime_factor(processing_seconds: float, audio_seconds: float) -> float | None:
    """Processing time divided by audio duration. Lower than 1.0 is faster than realtime."""
    if audio_seconds <= 0:
        return None
    return round(max(0.0, processing_seconds) / audio_seconds, 5)


def realtime_speed(processing_seconds: float, audio_seconds: float) -> float | None:
    """Audio duration divided by processing time. 10.0 means 10x realtime throughput."""
    if processing_seconds <= 0 or audio_seconds <= 0:
        return None
    return round(audio_seconds / processing_seconds, 3)


def _json_value(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float):
        return round(value, 6)
    return value


def append_perf(
    event: str,
    *,
    log_path: Path | None = None,
    **fields: Any,
) -> Path:
    """Append one machine-readable performance event to the normal Genre_test log."""
    payload = {"event": event}
    payload.update({key: _json_value(value) for key, value in fields.items()})
    return append_log(
        "PERF " + json.dumps(payload, ensure_ascii=False, sort_keys=True),
        path=log_path,
    )
