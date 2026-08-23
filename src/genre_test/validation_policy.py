from __future__ import annotations

RECHECK_FILTERS = {"all", "old_versions", "unstable"}


def should_recheck(
    filter_mode: str,
    current_version: str,
    latest_version: str | None,
    latest_confidence: str | None,
    latest_classification: str | None,
    latest_severity: str | None,
) -> bool:
    if filter_mode not in RECHECK_FILTERS:
        raise ValueError(f"Unknown recheck filter: {filter_mode}")
    if filter_mode == "all":
        return True
    if latest_version is None:
        return True
    if filter_mode == "old_versions":
        return latest_version != current_version
    return (
        latest_confidence != "high"
        or latest_classification == "hybrid"
        or latest_severity in {"SIGNIFICANT", "CRITICAL"}
    )
