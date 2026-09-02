from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

API_VERSION = "workstation-v1"
NAVIGATION_IDS = (
    "project",
    "analyze",
    "catalog",
    "search",
    "repair",
    "stems",
    "master",
    "compare",
    "delivery",
    "settings",
)
JobState = Literal["queued", "running", "cancelling", "cancelled", "succeeded", "failed"]
CapabilityState = Literal["available", "unavailable", "deferred"]


@dataclass(frozen=True)
class BackendCapability:
    key: str
    state: CapabilityState
    reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class JobStatus:
    job_id: str
    kind: str
    state: JobState
    progress: float | None
    cancellable: bool
    heartbeat_utc: str
    message: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ApiError:
    code: str
    message: str
    status: int

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": False,
            "error": {
                "code": self.code,
                "message": self.message,
            },
        }


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def validate_derived_output_path(source: Path, output: Path) -> Path:
    source_path = Path(source).expanduser().resolve(strict=False)
    output_path = Path(output).expanduser().resolve(strict=False)
    if source_path == output_path:
        raise ValueError("derived output must not overwrite the source path")
    return output_path
