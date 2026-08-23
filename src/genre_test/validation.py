from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from . import __version__
from .analyzer import GenreAnalyzer
from .audio import iter_audio_files
from .comparison import SEVERITY_ORDER, ComparisonResult, compare_results
from .convergence import ModeConvergence, compare_modes
from .history import HistoryDB
from .maest import DEFAULT_MODEL
from .models import AnalysisResult
from .report import write_json, write_validation_report, write_version_comparison_report
from .validation_policy import RECHECK_FILTERS, should_recheck

ProgressCallback = Callable[[int, int, str], None]


@dataclass(frozen=True)
class ScannedTrack:
    track_id: str
    path: Path
    duplicate_paths: tuple[Path, ...]


@dataclass(frozen=True)
class ValidationOutcome:
    track_id: str
    path: str
    status: str
    severity: str
    results: dict[str, AnalysisResult]
    convergence: ModeConvergence | None
    previous_comparisons: dict[str, ComparisonResult]

    def report_row(self) -> dict[str, object]:
        return {
            "track_id": self.track_id,
            "path": self.path,
            "status": self.status,
            "severity": self.severity,
            "modes": ",".join(self.results),
            "convergence": self.convergence.level if self.convergence else "",
            "resolved_genres": "; ".join(
                f"{mode}:{result.resolved_genre}" for mode, result in self.results.items()
            ),
            "versions": "; ".join(
                f"{mode}:{result.analyzer_version}" for mode, result in self.results.items()
            ),
            "notes": "; ".join(
                reason
                for comparison in self.previous_comparisons.values()
                for reason in comparison.reasons
            ),
        }


@dataclass(frozen=True)
class ValidationSessionResult:
    session_id: str
    scanned_tracks: int
    analyzed_tracks: int
    skipped_tracks: int
    duplicate_paths: int
    severity_counts: dict[str, int]
    outcomes: list[ValidationOutcome]
    json_report: str | None = None
    csv_report: str | None = None

    def summary_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "analyzer_version": __version__,
            "scanned_tracks": self.scanned_tracks,
            "analyzed_tracks": self.analyzed_tracks,
            "skipped_tracks": self.skipped_tracks,
            "duplicate_paths": self.duplicate_paths,
            "severity_counts": self.severity_counts,
        }


@dataclass(frozen=True)
class VersionComparisonResult:
    summary: dict[str, object]
    rows: list[dict[str, object]]
    json_report: str | None = None
    csv_report: str | None = None


class ValidationEngine:
    def __init__(
        self,
        history_path: Path | None = None,
        out_dir: Path = Path("results") / "validation",
        device: str = "auto",
        model_id: str = DEFAULT_MODEL,
        revision: str | None = None,
        top_k: int = 15,
    ) -> None:
        self.history = HistoryDB(history_path)
        self.out_dir = out_dir.expanduser().resolve()
        self.device = device
        self.model_id = model_id
        self.revision = revision
        self.top_k = top_k
        self._analyzer: GenreAnalyzer | None = None

    def _get_analyzer(self) -> GenreAnalyzer:
        if self._analyzer is None:
            self._analyzer = GenreAnalyzer(
                model_id=self.model_id,
                revision=self.revision,
                device=self.device,
                analysis_mode="auto",
                top_k=self.top_k,
            )
        return self._analyzer

    def scan_sources(
        self, sources: Iterable[Path], progress: ProgressCallback | None = None
    ) -> list[ScannedTrack]:
        paths: list[Path] = []
        seen_paths: set[str] = set()
        for source in sources:
            for path in iter_audio_files(source.expanduser()):
                resolved = path.resolve()
                key = str(resolved).casefold()
                if key not in seen_paths:
                    seen_paths.add(key)
                    paths.append(resolved)

        grouped: dict[str, list[Path]] = {}
        total = len(paths)
        for index, path in enumerate(paths, 1):
            if progress:
                progress(index, total, f"Идентификация: {path.name}")
            track_id = self.history.resolve_track_id(path)
            grouped.setdefault(track_id, []).append(path)

        return [
            ScannedTrack(track_id, group[0], tuple(group[1:]))
            for track_id, group in sorted(
                grouped.items(), key=lambda item: str(item[1][0]).casefold()
            )
        ]

    def recheck(
        self,
        sources: Iterable[Path],
        mode: str = "auto",
        compare_all_modes: bool = False,
        filter_mode: str = "all",
        progress: ProgressCallback | None = None,
    ) -> ValidationSessionResult:
        sources = [Path(source) for source in sources]
        if filter_mode not in RECHECK_FILTERS:
            raise ValueError(f"Unknown filter mode: {filter_mode}")
        modes = ["fast", "auto", "accurate"] if compare_all_modes else [mode]
        tracks = self.scan_sources(sources, progress)
        session_id = self.history.create_session(__version__, sources, modes, filter_mode)
        analyzer = self._get_analyzer()
        outcomes: list[ValidationOutcome] = []
        skipped = 0
        duplicate_paths = sum(len(track.duplicate_paths) for track in tracks)

        for index, track in enumerate(tracks, 1):
            reference_mode = "auto" if compare_all_modes else mode
            latest_info = self.history.latest_run_info(track.track_id, reference_mode)
            latest_severity = self.history.latest_severity(track.track_id)
            if not should_recheck(
                filter_mode,
                __version__,
                latest_info.analyzer_version if latest_info else None,
                latest_info.confidence if latest_info else None,
                latest_info.classification if latest_info else None,
                latest_severity,
            ):
                skipped += 1
                continue

            if progress:
                progress(index, len(tracks), f"Анализ: {track.path.name}")

            previous = {
                run_mode: self.history.latest_run(track.track_id, mode=run_mode)
                for run_mode in modes
            }
            if compare_all_modes:
                results = analyzer.analyze_modes(track.path, modes=modes, track_id=track.track_id)
            else:
                result = analyzer.analyze(
                    track.path, analysis_mode=mode, track_id=track.track_id
                )
                results = {mode: result}

            for result in results.values():
                write_json(result, self.out_dir / "runs")
                self.history.record_result(result, session_id=session_id)

            previous_comparisons: dict[str, ComparisonResult] = {}
            severities: list[str] = []
            for run_mode, result in results.items():
                old = previous.get(run_mode)
                if old and old.run_id and result.run_id:
                    comparison = compare_results(old, result)
                    previous_comparisons[run_mode] = comparison
                    severities.append(comparison.severity)
                    comparison_type = (
                        "version" if old.analyzer_version != result.analyzer_version else "rerun"
                    )
                    self.history.store_comparison(
                        track.track_id,
                        old.run_id,
                        result.run_id,
                        comparison,
                        comparison_type,
                    )

            convergence = compare_modes(results) if compare_all_modes else None
            if convergence:
                severities.append(convergence.worst_severity)
                for pair_name, comparison in convergence.comparisons.items():
                    left_mode, right_mode = pair_name.split("_vs_", 1)
                    left = results[left_mode]
                    right = results[right_mode]
                    if left.run_id and right.run_id:
                        self.history.store_comparison(
                            track.track_id,
                            left.run_id,
                            right.run_id,
                            comparison,
                            "mode",
                        )

            severity = (
                max(severities, key=lambda value: SEVERITY_ORDER[value])
                if severities
                else "STABLE"
            )
            status = "NEW" if not any(previous.values()) else "RECHECKED"
            outcomes.append(
                ValidationOutcome(
                    track_id=track.track_id,
                    path=str(track.path),
                    status=status,
                    severity=severity,
                    results=results,
                    convergence=convergence,
                    previous_comparisons=previous_comparisons,
                )
            )

        severity_counts = {name: 0 for name in SEVERITY_ORDER}
        for outcome in outcomes:
            severity_counts[outcome.severity] += 1

        provisional = ValidationSessionResult(
            session_id=session_id,
            scanned_tracks=len(tracks),
            analyzed_tracks=len(outcomes),
            skipped_tracks=skipped,
            duplicate_paths=duplicate_paths,
            severity_counts=severity_counts,
            outcomes=outcomes,
        )
        summary = provisional.summary_dict()
        rows = [outcome.report_row() for outcome in outcomes]
        json_report, csv_report = write_validation_report(summary, rows, self.out_dir)
        self.history.finish_session(
            session_id,
            {**summary, "json_report": str(json_report), "csv_report": str(csv_report)},
        )
        return ValidationSessionResult(
            session_id=session_id,
            scanned_tracks=len(tracks),
            analyzed_tracks=len(outcomes),
            skipped_tracks=skipped,
            duplicate_paths=duplicate_paths,
            severity_counts=severity_counts,
            outcomes=outcomes,
            json_report=str(json_report),
            csv_report=str(csv_report),
        )

    def import_history_sources(self, sources: Iterable[Path]) -> tuple[int, int]:
        json_paths: list[Path] = []
        seen: set[str] = set()
        for source in sources:
            source = source.expanduser()
            candidates = [source] if source.is_file() else source.rglob("*.genre*.json")
            for path in candidates:
                if path.is_file():
                    key = str(path.resolve()).casefold()
                    if key not in seen:
                        seen.add(key)
                        json_paths.append(path.resolve())
        return self.history.import_result_jsons(json_paths)

    def compare_versions(
        self,
        version_a: str,
        version_b: str,
        mode: str = "auto",
        write_reports: bool = True,
    ) -> VersionComparisonResult:
        rows: list[dict[str, object]] = []
        counts = {name: 0 for name in SEVERITY_ORDER}
        broad_matches = 0
        resolved_matches = 0
        tempo_equivalent = 0
        key_known = 0
        key_matches = 0

        for track_id in self.history.track_ids():
            selected_mode = None if mode == "any" else mode
            left = self.history.latest_run(
                track_id, mode=selected_mode, analyzer_version=version_a
            )
            right = self.history.latest_run(
                track_id, mode=selected_mode, analyzer_version=version_b
            )
            if not left or not right:
                continue
            comparison = compare_results(left, right)
            counts[comparison.severity] += 1
            broad_matches += int(comparison.broad_match)
            resolved_matches += int(comparison.resolved_match)
            tempo_equivalent += int(comparison.tempo_relation in {"same", "half-double"})
            if comparison.key_match is not None:
                key_known += 1
                key_matches += int(comparison.key_match)
            rows.append(
                {
                    "track_id": track_id,
                    "path": right.path or left.path,
                    "severity": comparison.severity,
                    "left_genre": left.resolved_genre,
                    "right_genre": right.resolved_genre,
                    "left_family": left.primary_genre,
                    "right_family": right.primary_genre,
                    "tempo_relation": comparison.tempo_relation,
                    "js_divergence": comparison.js_divergence,
                    "cosine_similarity": comparison.cosine_similarity,
                    "topn_weighted_overlap": comparison.topn_weighted_overlap,
                    "reasons": "; ".join(comparison.reasons),
                }
            )

        total = len(rows)

        def pct(value: int, denom: int = total) -> float:
            return round(100.0 * value / denom, 2) if denom else 0.0

        summary: dict[str, object] = {
            "version_a": version_a,
            "version_b": version_b,
            "mode": mode,
            "tracks_compared": total,
            "severity_counts": counts,
            "broad_family_match_pct": pct(broad_matches),
            "resolved_genre_match_pct": pct(resolved_matches),
            "tempo_equivalent_pct": pct(tempo_equivalent),
            "key_mode_match_pct": pct(key_matches, key_known),
            "key_mode_known": key_known,
        }

        json_report = None
        csv_report = None
        if write_reports:
            json_path, csv_path = write_version_comparison_report(summary, rows, self.out_dir)
            json_report = str(json_path)
            csv_report = str(csv_path)
        return VersionComparisonResult(summary, rows, json_report, csv_report)


def format_validation_session(result: ValidationSessionResult) -> str:
    counts = result.severity_counts
    lines = [
        f"Session: {result.session_id}",
        f"Scanned: {result.scanned_tracks}",
        f"Analyzed: {result.analyzed_tracks}",
        f"Skipped: {result.skipped_tracks}",
        f"Duplicate paths: {result.duplicate_paths}",
        "",
        "Drift / convergence:",
        f"STABLE: {counts['STABLE']}",
        f"MINOR: {counts['MINOR']}",
        f"SIGNIFICANT: {counts['SIGNIFICANT']}",
        f"CRITICAL: {counts['CRITICAL']}",
    ]
    if result.json_report:
        lines.append(f"JSON report: {result.json_report}")
    if result.csv_report:
        lines.append(f"CSV report: {result.csv_report}")
    for outcome in result.outcomes:
        convergence = (
            f", convergence={outcome.convergence.level}" if outcome.convergence else ""
        )
        genres = ", ".join(
            f"{mode}={item.resolved_genre}" for mode, item in outcome.results.items()
        )
        lines.append(
            f"\n[{outcome.severity}] {Path(outcome.path).name}{convergence}\n  {genres}"
        )
    return "\n".join(lines)


def format_version_comparison(result: VersionComparisonResult) -> str:
    summary = result.summary
    counts = summary["severity_counts"]
    lines = [
        f"Versions: {summary['version_a']} -> {summary['version_b']} ({summary['mode']})",
        f"Tracks compared: {summary['tracks_compared']}",
        f"Stable: {counts['STABLE']}",
        f"Minor: {counts['MINOR']}",
        f"Significant: {counts['SIGNIFICANT']}",
        f"Critical: {counts['CRITICAL']}",
        f"Resolved genre match: {summary['resolved_genre_match_pct']}%",
        f"Broad family match: {summary['broad_family_match_pct']}%",
        f"Tempo equivalent: {summary['tempo_equivalent_pct']}%",
        f"Key/mode match: {summary['key_mode_match_pct']}%",
    ]
    if result.json_report:
        lines.append(f"JSON report: {result.json_report}")
    if result.csv_report:
        lines.append(f"CSV report: {result.csv_report}")
    for row in result.rows:
        if row["severity"] != "STABLE":
            lines.append(
                f"\n[{row['severity']}] {Path(str(row['path'])).name}: "
                f"{row['left_genre']} -> {row['right_genre']} ({row['reasons']})"
            )
    return "\n".join(lines)
