from __future__ import annotations

import json
from dataclasses import dataclass

from . import __version__
from .history import HistoryDB, RunInfo
from .model_config import DEFAULT_MODEL, DEFAULT_MODEL_REVISION
from .models import AnalysisResult
from .runtime_meta import RESULT_SCHEMA_VERSION, current_git_commit


@dataclass(frozen=True)
class BuildInfo:
    analyzer_version: str
    git_commit: str | None
    schema_version: int
    model_id: str
    model_revision: str | None
    latest_analyzed_at: str = ""

    @property
    def key(self) -> str:
        payload = {
            "v": self.analyzer_version,
            "git": self.git_commit or "",
            "schema": self.schema_version,
            "model": self.model_id,
            "revision": self.model_revision or "",
        }
        return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))

    @property
    def short_commit(self) -> str:
        return (self.git_commit or "nogit")[:8]

    @property
    def short_model_revision(self) -> str:
        return (self.model_revision or "unversioned")[:8]

    @property
    def label(self) -> str:
        return (
            f"{self.analyzer_version} @ {self.short_commit} | "
            f"schema {self.schema_version} | model {self.short_model_revision}"
        )


class BuildAwareHistoryDB(HistoryDB):
    """History view that distinguishes persisted analyzer builds, not only semver."""

    @staticmethod
    def _build_clauses(build: BuildInfo) -> tuple[list[str], list[object]]:
        clauses = [
            "analyzer_version = ?",
            "schema_version = ?",
            "model_id = ?",
            "COALESCE(git_commit, '') = ?",
            "COALESCE(model_revision, '') = ?",
        ]
        params: list[object] = [
            build.analyzer_version,
            build.schema_version,
            build.model_id,
            build.git_commit or "",
            build.model_revision or "",
        ]
        return clauses, params

    def builds(self) -> list[BuildInfo]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT analyzer_version, git_commit, schema_version, model_id, model_revision,
                       MAX(analyzed_at) AS latest_analyzed_at
                FROM runs
                GROUP BY analyzer_version, COALESCE(git_commit, ''), schema_version,
                         model_id, COALESCE(model_revision, '')
                ORDER BY latest_analyzed_at, analyzer_version
                """
            ).fetchall()
        return [
            BuildInfo(
                analyzer_version=str(row["analyzer_version"]),
                git_commit=str(row["git_commit"]) if row["git_commit"] else None,
                schema_version=int(row["schema_version"]),
                model_id=str(row["model_id"]),
                model_revision=(str(row["model_revision"]) if row["model_revision"] else None),
                latest_analyzed_at=str(row["latest_analyzed_at"] or ""),
            )
            for row in rows
        ]

    def track_ids_for_build(self, build: BuildInfo, mode: str | None = None) -> set[str]:
        clauses, params = self._build_clauses(build)
        if mode:
            clauses.append("analysis_mode = ?")
            params.append(mode)
        query = "SELECT DISTINCT track_id FROM runs WHERE " + " AND ".join(clauses)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return {str(row["track_id"]) for row in rows}

    def runs_for_build(
        self,
        track_id: str,
        build: BuildInfo,
        mode: str | None = None,
        *,
        limit: int = 2,
    ) -> list[AnalysisResult]:
        clauses, params = self._build_clauses(build)
        clauses.insert(0, "track_id = ?")
        params.insert(0, track_id)
        if mode:
            clauses.append("analysis_mode = ?")
            params.append(mode)
        params.append(max(1, int(limit)))
        query = (
            "SELECT result_json FROM runs WHERE "
            + " AND ".join(clauses)
            + " ORDER BY analyzed_at DESC, rowid DESC LIMIT ?"
        )
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [AnalysisResult.from_dict(json.loads(row["result_json"])) for row in rows]

    def latest_run_for_build(
        self,
        track_id: str,
        build: BuildInfo,
        mode: str | None = None,
    ) -> AnalysisResult | None:
        runs = self.runs_for_build(track_id, build, mode, limit=1)
        return runs[0] if runs else None

    def latest_run_info(self, track_id: str, mode: str | None = None) -> RunInfo | None:
        clauses = ["track_id = ?"]
        params: list[object] = [track_id]
        if mode:
            clauses.append("analysis_mode = ?")
            params.append(mode)
        query = (
            "SELECT run_id, track_id, analyzer_version, analysis_mode, analyzed_at, confidence, "
            "classification, resolved_genre, primary_genre, git_commit, schema_version, "
            "model_id, model_revision FROM runs WHERE "
            + " AND ".join(clauses)
            + " ORDER BY analyzed_at DESC, rowid DESC LIMIT 1"
        )
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        if not row:
            return None
        build = BuildInfo(
            analyzer_version=str(row["analyzer_version"]),
            git_commit=str(row["git_commit"]) if row["git_commit"] else None,
            schema_version=int(row["schema_version"]),
            model_id=str(row["model_id"]),
            model_revision=(str(row["model_revision"]) if row["model_revision"] else None),
            latest_analyzed_at=str(row["analyzed_at"]),
        )
        return RunInfo(
            run_id=str(row["run_id"]),
            track_id=str(row["track_id"]),
            analyzer_version=build.key,
            analysis_mode=str(row["analysis_mode"]),
            analyzed_at=str(row["analyzed_at"]),
            confidence=str(row["confidence"] or ""),
            classification=str(row["classification"] or ""),
            resolved_genre=(str(row["resolved_genre"]) if row["resolved_genre"] else None),
            primary_genre=(str(row["primary_genre"]) if row["primary_genre"] else None),
        )


def current_build() -> BuildInfo:
    return BuildInfo(
        analyzer_version=__version__,
        git_commit=current_git_commit(),
        schema_version=RESULT_SCHEMA_VERSION,
        model_id=DEFAULT_MODEL,
        model_revision=DEFAULT_MODEL_REVISION,
    )


def should_recheck_build(
    filter_mode: str,
    _current_version: str,
    latest_build_key: str | None,
    latest_confidence: str | None,
    latest_classification: str | None,
    latest_severity: str | None,
) -> bool:
    if filter_mode not in {"all", "old_versions", "unstable"}:
        raise ValueError(f"Unknown recheck filter: {filter_mode}")
    if filter_mode == "all":
        return True
    if latest_build_key is None:
        return True
    if filter_mode == "old_versions":
        return latest_build_key != current_build().key
    return (
        latest_confidence != "high"
        or latest_classification == "hybrid"
        or latest_severity in {"SIGNIFICANT", "CRITICAL"}
    )


def install_validation_build_awareness() -> None:
    """Upgrade GUI Validation to build-aware freshness without changing the SQLite schema."""
    from . import validation, validation_gui

    validation.HistoryDB = BuildAwareHistoryDB
    validation.should_recheck = should_recheck_build
    validation_gui.HistoryDB = BuildAwareHistoryDB

    old_label = "Только результаты старых версий"
    new_label = "Неактуальные / отсутствующие результаты"
    filter_values = dict(validation_gui.FILTER_LABELS)
    filter_values.pop(old_label, None)
    filter_values = {new_label: "old_versions", **filter_values}
    validation_gui.FILTER_LABELS.clear()
    validation_gui.FILTER_LABELS.update(filter_values)

    original_tab = validation_gui.ValidationTab
    if getattr(original_tab, "_genre_test_build_aware", False):
        return

    class BuildAwareValidationTab(original_tab):
        _genre_test_build_aware = True

        def __init__(self, master) -> None:
            super().__init__(master)
            invalid_default = self.filter_var.get() not in validation_gui.FILTER_LABELS
            if self.filter_var.get() == old_label or invalid_default:
                self.filter_var.set(new_label)

    validation_gui.ValidationTab = BuildAwareValidationTab
