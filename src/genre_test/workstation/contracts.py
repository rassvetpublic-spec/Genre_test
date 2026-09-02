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
    """Return a normalized derived path while protecting source-file identity.

    Path equality alone is insufficient: an existing output may be a hard link to
    the source and therefore share the same inode/file identity.  Existing source
    and output files are compared with ``samefile`` as a second, fail-closed guard.
    """

    source_path = Path(source).expanduser().resolve(strict=False)
    output_path = Path(output).expanduser().resolve(strict=False)
    if source_path == output_path:
        raise ValueError("derived output must not overwrite the source path")

    if source_path.exists() and output_path.exists():
        try:
            same_file = source_path.samefile(output_path)
        except OSError as exc:
            raise ValueError("unable to verify derived output file identity") from exc
        if same_file:
            raise ValueError("derived output must not alias the source file")

    return output_path
