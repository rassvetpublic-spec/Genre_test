from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .comparison import ComparisonResult
from .models import AnalysisResult
from .runtime_meta import default_history_path, utc_now_iso
from .track_identity import identify_track

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS tracks (
    track_id TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    last_path TEXT,
    file_size INTEGER
);
CREATE TABLE IF NOT EXISTS file_locations (
    path TEXT PRIMARY KEY,
    track_id TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    last_seen_at TEXT NOT NULL,
    FOREIGN KEY(track_id) REFERENCES tracks(track_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS validation_sessions (
    session_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    analyzer_version TEXT NOT NULL,
    sources_json TEXT NOT NULL,
    modes_json TEXT NOT NULL,
    filter_mode TEXT NOT NULL,
    summary_json TEXT
);
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    track_id TEXT NOT NULL,
    session_id TEXT,
    analyzed_at TEXT NOT NULL,
    analyzer_version TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    analysis_mode TEXT NOT NULL,
    windows_analyzed INTEGER NOT NULL,
    window_seconds REAL NOT NULL,
    report_top_k INTEGER NOT NULL,
    internal_top_k INTEGER NOT NULL,
    model_id TEXT NOT NULL,
    model_revision TEXT,
    device TEXT,
    git_commit TEXT,
    source_path TEXT,
    primary_genre TEXT,
    primary_genre_score REAL,
    resolved_genre TEXT,
    classification TEXT,
    confidence TEXT,
    family_margin REAL,
    family_ratio REAL,
    style_margin REAL,
    secondary_genre TEXT,
    secondary_style TEXT,
    bpm REAL,
    key_name TEXT,
    key_mode TEXT,
    result_json TEXT NOT NULL,
    FOREIGN KEY(track_id) REFERENCES tracks(track_id) ON DELETE CASCADE,
    FOREIGN KEY(session_id) REFERENCES validation_sessions(session_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_runs_track_time ON runs(track_id, analyzed_at DESC);
CREATE INDEX IF NOT EXISTS idx_runs_version_mode ON runs(analyzer_version, analysis_mode);
CREATE TABLE IF NOT EXISTS style_scores (
    run_id TEXT NOT NULL,
    rank INTEGER NOT NULL,
    label TEXT NOT NULL,
    score REAL NOT NULL,
    PRIMARY KEY(run_id, rank),
    FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS broad_scores (
    run_id TEXT NOT NULL,
    rank INTEGER NOT NULL,
    label TEXT NOT NULL,
    score REAL NOT NULL,
    PRIMARY KEY(run_id, rank),
    FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS comparisons (
    comparison_id TEXT PRIMARY KEY,
    track_id TEXT NOT NULL,
    left_run_id TEXT NOT NULL,
    right_run_id TEXT NOT NULL,
    comparison_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    severity TEXT NOT NULL,
    broad_match INTEGER NOT NULL,
    resolved_match INTEGER NOT NULL,
    classification_match INTEGER NOT NULL,
    tempo_relation TEXT NOT NULL,
    key_match INTEGER,
    js_divergence REAL NOT NULL,
    cosine_similarity REAL NOT NULL,
    topn_weighted_overlap REAL NOT NULL,
    summary_json TEXT NOT NULL,
    FOREIGN KEY(track_id) REFERENCES tracks(track_id) ON DELETE CASCADE,
    FOREIGN KEY(left_run_id) REFERENCES runs(run_id) ON DELETE CASCADE,
    FOREIGN KEY(right_run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_comparisons_track_time
    ON comparisons(track_id, created_at DESC);
"""


@dataclass(frozen=True)
class RunInfo:
    run_id: str
    track_id: str
    analyzer_version: str
    analysis_mode: str
    analyzed_at: str
    confidence: str
    classification: str
    resolved_genre: str | None
    primary_genre: str | None


class HistoryDB:
    def __init__(self, path: Path | None = None) -> None:
        self.path = (path or default_history_path()).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)

    def resolve_track_id(self, path: Path) -> str:
        resolved = path.resolve()
        stat = resolved.stat()
        key = str(resolved)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT track_id, size_bytes, mtime_ns FROM file_locations WHERE path = ?",
                (key,),
            ).fetchone()
            if row and row["size_bytes"] == stat.st_size and row["mtime_ns"] == stat.st_mtime_ns:
                now = utc_now_iso()
                conn.execute(
                    "UPDATE file_locations SET last_seen_at = ? WHERE path = ?",
                    (now, key),
                )
                conn.execute(
                    "UPDATE tracks SET last_seen_at = ?, last_path = ? WHERE track_id = ?",
                    (now, key, row["track_id"]),
                )
                return str(row["track_id"])

        identity = identify_track(resolved)
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tracks(track_id, sha256, first_seen_at, last_seen_at, last_path, file_size)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(track_id) DO UPDATE SET
                    last_seen_at = excluded.last_seen_at,
                    last_path = excluded.last_path,
                    file_size = excluded.file_size
                """,
                (
                    identity.track_id,
                    identity.sha256,
                    now,
                    now,
                    identity.path,
                    identity.size_bytes,
                ),
            )
            conn.execute(
                """
                INSERT INTO file_locations(path, track_id, size_bytes, mtime_ns, last_seen_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    track_id = excluded.track_id,
                    size_bytes = excluded.size_bytes,
                    mtime_ns = excluded.mtime_ns,
                    last_seen_at = excluded.last_seen_at
                """,
                (key, identity.track_id, stat.st_size, stat.st_mtime_ns, now),
            )
        return identity.track_id

    def create_session(
        self,
        analyzer_version: str,
        sources: Iterable[Path],
        modes: Iterable[str],
        filter_mode: str,
    ) -> str:
        session_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO validation_sessions(
                    session_id, started_at, analyzer_version, sources_json, modes_json, filter_mode
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    utc_now_iso(),
                    analyzer_version,
                    json.dumps([str(Path(p).resolve()) for p in sources], ensure_ascii=False),
                    json.dumps(list(modes), ensure_ascii=False),
                    filter_mode,
                ),
            )
        return session_id

    def finish_session(self, session_id: str, summary: dict[str, object]) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE validation_sessions SET finished_at = ?, summary_json = ? WHERE session_id = ?",
                (utc_now_iso(), json.dumps(summary, ensure_ascii=False), session_id),
            )

    def record_result(self, result: AnalysisResult, session_id: str | None = None) -> str:
        if not result.track_id:
            source = Path(result.path)
            if not source.exists():
                raise ValueError("AnalysisResult has no track_id and source file is unavailable")
            track_id = self.resolve_track_id(source)
            result = replace(result, track_id=track_id, source_file_size=source.stat().st_size)
        if not result.run_id:
            result = replace(result, run_id=str(uuid.uuid4()))
        if not result.analyzed_at:
            result = replace(result, analyzed_at=utc_now_iso())

        track_id = str(result.track_id)
        sha256 = track_id.split(":", 1)[1] if track_id.startswith("sha256:") else track_id
        now = utc_now_iso()
        source = Path(result.path)
        size = result.source_file_size
        if size is None and source.exists():
            size = source.stat().st_size

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tracks(track_id, sha256, first_seen_at, last_seen_at, last_path, file_size)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(track_id) DO UPDATE SET
                    last_seen_at = excluded.last_seen_at,
                    last_path = excluded.last_path,
                    file_size = COALESCE(excluded.file_size, tracks.file_size)
                """,
                (track_id, sha256, now, now, result.path, size),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO runs(
                    run_id, track_id, session_id, analyzed_at, analyzer_version, schema_version,
                    analysis_mode, windows_analyzed, window_seconds, report_top_k, internal_top_k,
                    model_id, model_revision, device, git_commit, source_path, primary_genre,
                    primary_genre_score, resolved_genre, classification, confidence, family_margin,
                    family_ratio, style_margin, secondary_genre, secondary_style, bpm, key_name,
                    key_mode, result_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.run_id,
                    track_id,
                    session_id,
                    result.analyzed_at,
                    result.analyzer_version,
                    result.schema_version,
                    result.analysis_mode,
                    result.windows_analyzed,
                    result.window_seconds,
                    result.report_top_k,
                    result.internal_top_k,
                    result.model_id,
                    result.model_revision,
                    result.device,
                    result.git_commit,
                    result.path,
                    result.primary_genre,
                    result.primary_genre_score,
                    result.resolved_genre,
                    result.classification,
                    result.confidence,
                    result.family_margin,
                    result.family_ratio,
                    result.style_margin,
                    result.secondary_genre,
                    result.secondary_style,
                    result.audio_features.bpm,
                    result.audio_features.key,
                    result.audio_features.mode,
                    json.dumps(result.to_dict(), ensure_ascii=False),
                ),
            )
            conn.execute("DELETE FROM style_scores WHERE run_id = ?", (result.run_id,))
            conn.execute("DELETE FROM broad_scores WHERE run_id = ?", (result.run_id,))
            conn.executemany(
                "INSERT INTO style_scores(run_id, rank, label, score) VALUES (?, ?, ?, ?)",
                [
                    (result.run_id, rank, item.label, item.score)
                    for rank, item in enumerate(result.top_styles, 1)
                ],
            )
            conn.executemany(
                "INSERT INTO broad_scores(run_id, rank, label, score) VALUES (?, ?, ?, ?)",
                [
                    (result.run_id, rank, item.label, item.score)
                    for rank, item in enumerate(result.broad_genres, 1)
                ],
            )
        return str(result.run_id)

    def get_run(self, run_id: str) -> AnalysisResult | None:
        with self._connect() as conn:
            row = conn.execute("SELECT result_json FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if not row:
            return None
        return AnalysisResult.from_dict(json.loads(row["result_json"]))

    def latest_run(
        self,
        track_id: str,
        mode: str | None = None,
        analyzer_version: str | None = None,
        exclude_run_id: str | None = None,
    ) -> AnalysisResult | None:
        clauses = ["track_id = ?"]
        params: list[object] = [track_id]
        if mode:
            clauses.append("analysis_mode = ?")
            params.append(mode)
        if analyzer_version:
            clauses.append("analyzer_version = ?")
            params.append(analyzer_version)
        if exclude_run_id:
            clauses.append("run_id != ?")
            params.append(exclude_run_id)
        query = (
            "SELECT result_json FROM runs WHERE "
            + " AND ".join(clauses)
            + " ORDER BY analyzed_at DESC, rowid DESC LIMIT 1"
        )
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        return AnalysisResult.from_dict(json.loads(row["result_json"])) if row else None

    def latest_run_info(self, track_id: str, mode: str | None = None) -> RunInfo | None:
        clauses = ["track_id = ?"]
        params: list[object] = [track_id]
        if mode:
            clauses.append("analysis_mode = ?")
            params.append(mode)
        query = (
            "SELECT run_id, track_id, analyzer_version, analysis_mode, analyzed_at, confidence, "
            "classification, resolved_genre, primary_genre FROM runs WHERE "
            + " AND ".join(clauses)
            + " ORDER BY analyzed_at DESC, rowid DESC LIMIT 1"
        )
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        return RunInfo(**dict(row)) if row else None

    def latest_severity(self, track_id: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT severity FROM comparisons WHERE track_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 1",
                (track_id,),
            ).fetchone()
        return str(row["severity"]) if row else None

    def store_comparison(
        self,
        track_id: str,
        left_run_id: str,
        right_run_id: str,
        comparison: ComparisonResult,
        comparison_type: str,
    ) -> str:
        comparison_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO comparisons(
                    comparison_id, track_id, left_run_id, right_run_id, comparison_type,
                    created_at, severity, broad_match, resolved_match, classification_match,
                    tempo_relation, key_match, js_divergence, cosine_similarity,
                    topn_weighted_overlap, summary_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    comparison_id,
                    track_id,
                    left_run_id,
                    right_run_id,
                    comparison_type,
                    utc_now_iso(),
                    comparison.severity,
                    int(comparison.broad_match),
                    int(comparison.resolved_match),
                    int(comparison.classification_match),
                    comparison.tempo_relation,
                    None if comparison.key_match is None else int(comparison.key_match),
                    comparison.js_divergence,
                    comparison.cosine_similarity,
                    comparison.topn_weighted_overlap,
                    json.dumps(comparison.to_dict(), ensure_ascii=False),
                ),
            )
        return comparison_id

    def versions(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT analyzer_version FROM runs ORDER BY analyzer_version"
            ).fetchall()
        return [str(row["analyzer_version"]) for row in rows]

    def track_ids(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT track_id FROM tracks ORDER BY first_seen_at").fetchall()
        return [str(row["track_id"]) for row in rows]

    def import_result_json(self, json_path: Path) -> AnalysisResult | None:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "audio_features" not in data:
            return None
        result = AnalysisResult.from_dict(data)
        source = Path(result.path)
        if not result.track_id:
            if not source.exists():
                return None
            track_id = self.resolve_track_id(source)
            result = replace(result, track_id=track_id, source_file_size=source.stat().st_size)
        if not result.analyzed_at:
            mtime = datetime.fromtimestamp(json_path.stat().st_mtime, tz=timezone.utc)
            result = replace(
                result,
                analyzed_at=mtime.isoformat(timespec="seconds").replace("+00:00", "Z"),
            )
        if not result.run_id:
            legacy_key = (
                f"{json_path.resolve()}:{json_path.stat().st_mtime_ns}:"
                f"{json_path.stat().st_size}"
            )
            result = replace(
                result,
                run_id=str(uuid.uuid5(uuid.NAMESPACE_URL, legacy_key)),
            )
        self.record_result(result)
        return result

    def import_result_jsons(self, paths: Iterable[Path]) -> tuple[int, int]:
        imported = 0
        skipped = 0
        for path in paths:
            try:
                result = self.import_result_json(path)
            except (OSError, ValueError, json.JSONDecodeError):
                result = None
            if result is None:
                skipped += 1
            else:
                imported += 1
        return imported, skipped
