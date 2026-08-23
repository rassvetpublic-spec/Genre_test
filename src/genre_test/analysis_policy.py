from __future__ import annotations

ANALYSIS_MODES = {"auto", "fast", "accurate", "expert"}


def duration_window_target(duration_s: float) -> int:
    """Choose the maximum representative-window count from track duration."""
    if duration_s < 60:
        return 1
    if duration_s < 120:
        return 3
    if duration_s < 210:
        return 5
    if duration_s < 300:
        return 7
    if duration_s < 420:
        return 9
    return 11


def spread_indices(total: int, count: int) -> list[int]:
    """Return stable, approximately uniform indices including both ends."""
    if total <= 0 or count <= 0:
        return []
    if count >= total:
        return list(range(total))
    if count == 1:
        return [total // 2]

    indices = [round(i * (total - 1) / (count - 1)) for i in range(count)]
    return list(dict.fromkeys(indices))


def needs_more_auto_windows(classification: str, confidence: str) -> bool:
    """Expand Auto analysis unless the current result is a stable high-confidence primary."""
    return classification == "hybrid" or confidence != "high"
