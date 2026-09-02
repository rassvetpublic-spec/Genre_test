from __future__ import annotations

import importlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from uuid import uuid4

from .. import __version__
from .contracts import API_VERSION, NAVIGATION_IDS, BackendCapability, JobStatus, utc_now_iso
from .i18n import catalog, normalize_language
from .settings import SettingsStore

DONOR_REPOSITORY = "https://github.com/henricksmedia/shimmer"
DONOR_REVISION = "ff8344ae1a77bd7eb5be46b55c83813e923d3d2c"
DONOR_CLASSIFICATION = "REIMPLEMENT_FROM_PINNED_UI_REQUIREMENTS"


@dataclass
class WorkstationService:
    settings_store: SettingsStore = field(default_factory=SettingsStore)
    started_at: float = field(default_factory=time.time)
    _jobs: dict[str, JobStatus] = field(default_factory=dict, init=False, repr=False)
    _lock: RLock = field(default_factory=RLock, init=False, repr=False)

    def health(self) -> dict[str, object]:
        return {
            "ok": True,
            "api_version": API_VERSION,
            "app_version": __version__,
            "surface": "workstation-p1",
            "localhost_only": True,
            "uptime_seconds": round(max(0.0, time.time() - self.started_at), 3),
            "donor": {
                "repository": DONOR_REPOSITORY,
                "revision": DONOR_REVISION,
                "classification": DONOR_CLASSIFICATION,
                "direct_code_port": False,
            },
        }

    def navigation(self) -> dict[str, object]:
        return {
            "items": [
                {
                    "id": item,
                    "label_key": f"nav.{item}",
                    "phase": "p1" if item in {"project", "settings"} else "deferred",
                }
                for item in NAVIGATION_IDS
            ]
        }

    def capabilities(self) -> dict[str, object]:
        capabilities = [
            BackendCapability("workstation_shell", "available"),
            BackendCapability("runtime_hud", "available"),
            BackendCapability("retrieval_status", "available"),
            BackendCapability("analysis", "deferred", "Workstation P2"),
            BackendCapability("catalog", "deferred", "Workstation P2.2"),
            BackendCapability("search", "deferred", "Workstation P2.2"),
            BackendCapability("compare_transport", "deferred", "Workstation P3"),
            BackendCapability("repair", "deferred", "Workstation P5"),
            BackendCapability("stems", "deferred", "Workstation P6"),
            BackendCapability("mastering", "deferred", "Workstation P7"),
            BackendCapability("delivery", "deferred", "Workstation P8"),
        ]
        return {"items": [item.to_dict() for item in capabilities]}

    def runtime(self) -> dict[str, object]:
        module = importlib.import_module("genre_test.workstation.runtime_adapter")
        return {"ok": True, "runtime": module.collect_runtime_hud()}

    def retrieval_status(self) -> dict[str, object]:
        module = importlib.import_module("genre_test.workstation.retrieval_adapter")
        return module.collect_retrieval_status()

    def settings(self) -> dict[str, object]:
        return self.settings_store.load().to_dict()

    def set_language(self, language: str) -> dict[str, object]:
        return self.settings_store.save_language(language).to_dict()

    def translations(self, language: str | None) -> dict[str, object]:
        selected = normalize_language(language)
        return {"language": selected, "strings": catalog(selected)}

    def list_jobs(self) -> dict[str, object]:
        with self._lock:
            jobs = [job.to_dict() for _, job in sorted(self._jobs.items())]
        return {"items": jobs}

    def create_contract_job(self, kind: str = "contract_stub") -> dict[str, object]:
        """Create a lightweight contract-only job; no domain backend is executed in P1."""
        job = JobStatus(
            job_id=str(uuid4()),
            kind=kind,
            state="queued",
            progress=0.0,
            cancellable=True,
            heartbeat_utc=utc_now_iso(),
            message="P1 contract stub; no domain backend was executed",
        )
        with self._lock:
            self._jobs[job.job_id] = job
        return job.to_dict()

    def get_job(self, job_id: str) -> dict[str, object] | None:
        with self._lock:
            job = self._jobs.get(job_id)
        return None if job is None else job.to_dict()

    def cancel_job(self, job_id: str) -> dict[str, object] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            if job.state in {"cancelled", "succeeded", "failed"}:
                return job.to_dict()
            cancelled = JobStatus(
                job_id=job.job_id,
                kind=job.kind,
                state="cancelled",
                progress=job.progress,
                cancellable=False,
                heartbeat_utc=utc_now_iso(),
                message="Cancelled before domain backend execution",
            )
            self._jobs[job_id] = cancelled
        return cancelled.to_dict()


def validate_project_output(source: str | Path, output: str | Path) -> str:
    from .contracts import validate_derived_output_path

    return str(validate_derived_output_path(Path(source), Path(output)))
