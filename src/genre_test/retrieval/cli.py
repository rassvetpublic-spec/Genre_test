from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from ..runtime_meta import default_history_path, default_state_dir, project_root
from .benchmark import run_benchmark_suite, write_benchmark_reports
from .catalog_acceptance import (
    catalog_acceptance_report,
    retry_missing_full_embeddings,
    write_catalog_acceptance_reports,
)
from .clamp3_sidecar_backend import (
    Clamp3SidecarBackend,
    Clamp3SidecarError,
    default_clamp3_backend_info,
)
from .contracts import SearchFilter
from .export import write_search_csv, write_search_json
from .segments import (
    index_segments,
    search_custom_interval,
    search_representative_track,
    segment_status,
)
from .service import (
    SearchResult,
    index_catalog,
    index_status,
    rebuild_catalog,
    search_audio,
    search_text,
)
from .storage import RetrievalStore

EXIT_OK = 0
EXIT_BACKEND_UNAVAILABLE = 20
EXIT_INDEX_EMPTY = 21
EXIT_INVALID_QUERY = 22
EXIT_SOURCE_ERROR = 23
EXIT_INTERNAL_ERROR = 70
EXIT_INTERRUPTED = 130

app = typer.Typer(
    no_args_is_help=True,
    help="Genre_test v0.5 local CLaMP retrieval catalog and exact-search tools",
)
console = Console()


def _default_db() -> Path:
    return default_state_dir() / "retrieval.sqlite3"


def _default_report_prefix(stem: str) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return default_state_dir() / "logs" / f"{stem}_{stamp}"


def _split_values(value: str | None) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _filters(
    *,
    family: str | None,
    genre: str | None,
    key: str | None,
    vocal: str | None,
    mood: str | None,
    instrument: str | None,
    production: str | None,
    source_folder: str | None,
    bpm_min: float | None,
    bpm_max: float | None,
    min_confidence: float | None,
) -> SearchFilter:
    return SearchFilter(
        families=_split_values(family),
        genres=_split_values(genre),
        keys=_split_values(key),
        vocals=_split_values(vocal),
        moods=_split_values(mood),
        instruments=_split_values(instrument),
        production=_split_values(production),
        source_folders=_split_values(source_folder),
        bpm_min=bpm_min,
        bpm_max=bpm_max,
        min_confidence=min_confidence,
    )


def _print_json(payload: object) -> None:
    console.print(json.dumps(payload, ensure_ascii=False, indent=2))


def _progress(current: int, total: int, message: str) -> None:
    console.print(f"[{current}/{total}] {message}")


def _export(
    result: SearchResult,
    *,
    json_out: Path | None,
    csv_out: Path | None,
) -> None:
    if json_out is not None:
        target = write_search_json(result, json_out)
        console.print(f"JSON: {target}")
    if csv_out is not None:
        target = write_search_csv(result, csv_out)
        console.print(f"CSV: {target}")


@app.command("retrieval-index-status", hidden=True)
@app.command("status")
def status_command(
    db: Annotated[Path | None, typer.Option("--db", help="Retrieval SQLite path")] = None,
    history: Annotated[
        Path | None,
        typer.Option("--history", help="Analysis history SQLite path"),
    ] = None,
) -> None:
    """Show current catalog/cache/stale/corruption status without starting CLaMP."""
    store = RetrievalStore(db or _default_db())
    info = default_clamp3_backend_info()
    status = index_status(
        store=store,
        history_path=history or default_history_path(),
        backend_fingerprint=info.fingerprint,
    )
    _print_json(status.to_dict())


@app.command("retrieval-index", hidden=True)
@app.command("index")
def index_command(
    db: Annotated[Path | None, typer.Option("--db")] = None,
    history: Annotated[Path | None, typer.Option("--history")] = None,
    limit: Annotated[
        int | None,
        typer.Option("--limit", min=1, help="Pilot: process only first N catalog tracks"),
    ] = None,
) -> None:
    """Incrementally index missing tracks; completed rows are resumable cache hits."""
    store = RetrievalStore(db or _default_db())
    with Clamp3SidecarBackend.from_repo_defaults(
        project_root(), request_timeout_s=900.0
    ) as backend:
        report = index_catalog(
            store=store,
            history_path=history or default_history_path(),
            backend=backend,
            progress=_progress,
            limit=limit,
        )
    _print_json(report.to_dict())


@app.command("retrieval-rebuild", hidden=True)
@app.command("rebuild")
def rebuild_command(
    db: Annotated[Path | None, typer.Option("--db")] = None,
    history: Annotated[Path | None, typer.Option("--history")] = None,
) -> None:
    """Force a full rebuild for the active backend fingerprint only."""
    store = RetrievalStore(db or _default_db())
    with Clamp3SidecarBackend.from_repo_defaults(
        project_root(), request_timeout_s=900.0
    ) as backend:
        report = rebuild_catalog(
            store=store,
            history_path=history or default_history_path(),
            backend=backend,
            progress=_progress,
        )
    _print_json(report.to_dict())


def _search_options(
    *,
    family: str | None,
    genre: str | None,
    key: str | None,
    vocal: str | None,
    mood: str | None,
    instrument: str | None,
    production: str | None,
    source_folder: str | None,
    bpm_min: float | None,
    bpm_max: float | None,
    min_confidence: float | None,
) -> SearchFilter:
    return _filters(
        family=family,
        genre=genre,
        key=key,
        vocal=vocal,
        mood=mood,
        instrument=instrument,
        production=production,
        source_folder=source_folder,
        bpm_min=bpm_min,
        bpm_max=bpm_max,
        min_confidence=min_confidence,
    )


@app.command("retrieval-search-text", hidden=True)
@app.command("search-text")
def search_text_command(
    text: Annotated[str, typer.Argument(help="Native UTF-8 text query")],
    db: Annotated[Path | None, typer.Option("--db")] = None,
    history: Annotated[Path | None, typer.Option("--history")] = None,
    language: Annotated[str | None, typer.Option("--language")] = "ru",
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=1000)] = 20,
    family: Annotated[str | None, typer.Option("--family", help="Comma-separated")] = None,
    genre: Annotated[str | None, typer.Option("--genre", help="Comma-separated")] = None,
    key: Annotated[str | None, typer.Option("--key", help="Comma-separated, e.g. B minor")] = None,
    vocal: Annotated[str | None, typer.Option("--vocal", help="Comma-separated")] = None,
    mood: Annotated[str | None, typer.Option("--mood", help="Comma-separated")] = None,
    instrument: Annotated[
        str | None,
        typer.Option("--instrument", help="Comma-separated"),
    ] = None,
    production: Annotated[
        str | None,
        typer.Option("--production", help="Comma-separated"),
    ] = None,
    source_folder: Annotated[
        str | None,
        typer.Option("--source-folder", help="Comma-separated roots"),
    ] = None,
    bpm_min: Annotated[float | None, typer.Option("--bpm-min", min=0)] = None,
    bpm_max: Annotated[float | None, typer.Option("--bpm-max", min=0)] = None,
    min_confidence: Annotated[
        float | None,
        typer.Option("--min-confidence", min=0, max=1),
    ] = None,
    json_out: Annotated[Path | None, typer.Option("--json-out")] = None,
    csv_out: Annotated[Path | None, typer.Option("--csv-out")] = None,
) -> None:
    """Search catalog audio embeddings with a native Russian/multilingual text query."""
    filters = _search_options(
        family=family,
        genre=genre,
        key=key,
        vocal=vocal,
        mood=mood,
        instrument=instrument,
        production=production,
        source_folder=source_folder,
        bpm_min=bpm_min,
        bpm_max=bpm_max,
        min_confidence=min_confidence,
    )
    store = RetrievalStore(db or _default_db())
    with Clamp3SidecarBackend.from_repo_defaults(
        project_root(), request_timeout_s=900.0
    ) as backend:
        result = search_text(
            store=store,
            history_path=history or default_history_path(),
            backend=backend,
            text=text,
            language=language,
            top_k=top_k,
            filters=filters,
        )
    _print_json(result.to_dict())
    _export(result, json_out=json_out, csv_out=csv_out)


@app.command("retrieval-search-audio", hidden=True)
@app.command("search-audio")
def search_audio_command(
    audio: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, readable=True, help="Audio query file"),
    ],
    db: Annotated[Path | None, typer.Option("--db")] = None,
    history: Annotated[Path | None, typer.Option("--history")] = None,
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=1000)] = 20,
    include_self: Annotated[bool, typer.Option("--include-self")] = False,
    family: Annotated[str | None, typer.Option("--family", help="Comma-separated")] = None,
    genre: Annotated[str | None, typer.Option("--genre", help="Comma-separated")] = None,
    key: Annotated[str | None, typer.Option("--key", help="Comma-separated")] = None,
    vocal: Annotated[str | None, typer.Option("--vocal", help="Comma-separated")] = None,
    mood: Annotated[str | None, typer.Option("--mood", help="Comma-separated")] = None,
    instrument: Annotated[
        str | None,
        typer.Option("--instrument", help="Comma-separated"),
    ] = None,
    production: Annotated[
        str | None,
        typer.Option("--production", help="Comma-separated"),
    ] = None,
    source_folder: Annotated[
        str | None,
        typer.Option("--source-folder", help="Comma-separated roots"),
    ] = None,
    bpm_min: Annotated[float | None, typer.Option("--bpm-min", min=0)] = None,
    bpm_max: Annotated[float | None, typer.Option("--bpm-max", min=0)] = None,
    min_confidence: Annotated[
        float | None,
        typer.Option("--min-confidence", min=0, max=1),
    ] = None,
    json_out: Annotated[Path | None, typer.Option("--json-out")] = None,
    csv_out: Annotated[Path | None, typer.Option("--csv-out")] = None,
) -> None:
    """Search catalog by full-track audio similarity."""
    filters = _search_options(
        family=family,
        genre=genre,
        key=key,
        vocal=vocal,
        mood=mood,
        instrument=instrument,
        production=production,
        source_folder=source_folder,
        bpm_min=bpm_min,
        bpm_max=bpm_max,
        min_confidence=min_confidence,
    )
    store = RetrievalStore(db or _default_db())
    with Clamp3SidecarBackend.from_repo_defaults(
        project_root(), request_timeout_s=900.0
    ) as backend:
        result = search_audio(
            store=store,
            history_path=history or default_history_path(),
            backend=backend,
            audio_path=audio,
            top_k=top_k,
            filters=filters,
            exclude_self=not include_self,
        )
    _print_json(result.to_dict())
    _export(result, json_out=json_out, csv_out=csv_out)


@app.command("retrieval-search-history", hidden=True)
@app.command("history")
def history_command(
    db: Annotated[Path | None, typer.Option("--db")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=1000)] = 50,
) -> None:
    """Show local retrieval-query history stored separately from analysis history."""
    records = RetrievalStore(db or _default_db()).search_history(limit=limit)
    _print_json([asdict_record(record) for record in records])


def asdict_record(record: object) -> dict[str, object]:
    return {
        "query_id": getattr(record, "query_id"),
        "query_type": getattr(record, "query_type"),
        "backend_fingerprint": getattr(record, "backend_fingerprint"),
        "query_text": getattr(record, "query_text"),
        "language": getattr(record, "language"),
        "query_track_id": getattr(record, "query_track_id"),
        "top_k": getattr(record, "top_k"),
        "filters": getattr(record, "filters"),
        "embedding_seconds": getattr(record, "embedding_seconds"),
        "ranking_seconds": getattr(record, "ranking_seconds"),
        "result_count": getattr(record, "result_count"),
        "created_at": getattr(record, "created_at"),
    }


@app.command("segment-status")
def segment_status_command(
    db: Annotated[Path | None, typer.Option("--db")] = None,
    history: Annotated[Path | None, typer.Option("--history")] = None,
) -> None:
    """Show segment/representative cache state without starting the model."""
    info = default_clamp3_backend_info()
    report = segment_status(
        store=RetrievalStore(db or _default_db()),
        history_path=history or default_history_path(),
        backend_fingerprint=info.fingerprint,
    )
    _print_json(report.to_dict())


@app.command("segment-index")
def segment_index_command(
    db: Annotated[Path | None, typer.Option("--db")] = None,
    history: Annotated[Path | None, typer.Option("--history")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1)] = 50,
    all_tracks: Annotated[
        bool,
        typer.Option("--all", help="Explicitly allow full-catalog segment indexing"),
    ] = False,
) -> None:
    """Index a bounded segment subset; use --all only after subset cost review."""
    selected_limit = None if all_tracks else limit
    store = RetrievalStore(db or _default_db())
    with Clamp3SidecarBackend.from_repo_defaults(
        project_root(), request_timeout_s=900.0
    ) as backend:
        report = index_segments(
            store=store,
            history_path=history or default_history_path(),
            backend=backend,
            limit=selected_limit,
            progress=_progress,
        )
    _print_json(report.to_dict())


@app.command("search-representative")
def search_representative_command(
    track_id: Annotated[str, typer.Argument()],
    target_scope: Annotated[str, typer.Option("--target-scope")] = "full",
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=1000)] = 20,
    db: Annotated[Path | None, typer.Option("--db")] = None,
    history: Annotated[Path | None, typer.Option("--history")] = None,
) -> None:
    """Search from a persisted representative segment."""
    store = RetrievalStore(db or _default_db())
    with Clamp3SidecarBackend.from_repo_defaults(project_root()) as backend:
        result = search_representative_track(
            store=store,
            history_path=history or default_history_path(),
            backend=backend,
            track_id=track_id,
            target_scope=target_scope,
            top_k=top_k,
        )
    _print_json(result.to_dict())


@app.command("search-segment")
def search_segment_command(
    audio: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)],
    start_s: Annotated[float, typer.Argument(min=0)],
    end_s: Annotated[float, typer.Argument(min=0)],
    target_scope: Annotated[str, typer.Option("--target-scope")] = "full",
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=1000)] = 20,
    db: Annotated[Path | None, typer.Option("--db")] = None,
    history: Annotated[Path | None, typer.Option("--history")] = None,
) -> None:
    """Search from an explicit audio interval."""
    store = RetrievalStore(db or _default_db())
    with Clamp3SidecarBackend.from_repo_defaults(project_root()) as backend:
        result = search_custom_interval(
            store=store,
            history_path=history or default_history_path(),
            backend=backend,
            audio_path=audio,
            start_s=start_s,
            end_s=end_s,
            target_scope=target_scope,
            top_k=top_k,
        )
    _print_json(result.to_dict())


@app.command("catalog-audit")
def catalog_audit_command(
    db: Annotated[Path | None, typer.Option("--db")] = None,
    history: Annotated[Path | None, typer.Option("--history")] = None,
    out_prefix: Annotated[Path | None, typer.Option("--out-prefix")] = None,
) -> None:
    """Generate the #39 full-catalog coverage/acceptance report without starting CLaMP."""
    info = default_clamp3_backend_info()
    report = catalog_acceptance_report(
        store=RetrievalStore(db or _default_db()),
        history_path=history or default_history_path(),
        backend_fingerprint=info.fingerprint,
    )
    targets = write_catalog_acceptance_reports(
        report,
        out_prefix or _default_report_prefix("retrieval_catalog_acceptance"),
    )
    _print_json({"report": report.to_dict(), "files": {k: str(v) for k, v in targets.items()}})


@app.command("retry-missing")
def retry_missing_command(
    db: Annotated[Path | None, typer.Option("--db")] = None,
    history: Annotated[Path | None, typer.Option("--history")] = None,
    limit: Annotated[int | None, typer.Option("--limit", min=1)] = None,
) -> None:
    """Retry only readable catalog tracks that still lack the active full embedding."""
    store = RetrievalStore(db or _default_db())
    history_path = history or default_history_path()
    info = default_clamp3_backend_info()
    audit = catalog_acceptance_report(
        store=store,
        history_path=history_path,
        backend_fingerprint=info.fingerprint,
    )
    track_ids = audit.retry_track_ids[:limit] if limit is not None else audit.retry_track_ids
    with Clamp3SidecarBackend.from_repo_defaults(
        project_root(), request_timeout_s=900.0
    ) as backend:
        result = retry_missing_full_embeddings(
            store=store,
            history_path=history_path,
            backend=backend,
            track_ids=track_ids,
        )
    _print_json(result)


@app.command("benchmark-run")
def benchmark_run_command(
    suite: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)],
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=100)] = 10,
    db: Annotated[Path | None, typer.Option("--db")] = None,
    history: Annotated[Path | None, typer.Option("--history")] = None,
    out_prefix: Annotated[Path | None, typer.Option("--out-prefix")] = None,
) -> None:
    """Run a reviewed #36 retrieval benchmark and write JSON/CSV/Markdown."""
    store = RetrievalStore(db or _default_db())
    with Clamp3SidecarBackend.from_repo_defaults(
        project_root(), request_timeout_s=900.0
    ) as backend:
        report = run_benchmark_suite(
            suite_path=suite,
            store=store,
            history_path=history or default_history_path(),
            backend=backend,
            top_k=top_k,
        )
    targets = write_benchmark_reports(
        report,
        out_prefix or _default_report_prefix("retrieval_benchmark"),
    )
    _print_json({"report": report.to_dict(), "files": {k: str(v) for k, v in targets.items()}})


@app.command("exit-codes")
def exit_codes_command() -> None:
    """Print the stable v0.5 retrieval automation exit-code contract."""
    _print_json(
        {
            "success": EXIT_OK,
            "backend_unavailable": EXIT_BACKEND_UNAVAILABLE,
            "index_empty_or_required_embedding_missing": EXIT_INDEX_EMPTY,
            "invalid_query_or_arguments": EXIT_INVALID_QUERY,
            "source_file_error": EXIT_SOURCE_ERROR,
            "internal_error": EXIT_INTERNAL_ERROR,
            "interrupted_safe_stop": EXIT_INTERRUPTED,
        }
    )


def _map_value_error(exc: ValueError) -> int:
    text = str(exc).casefold()
    if "no full-track embeddings" in text or "no representative" in text or "missing embedding" in text:
        return EXIT_INDEX_EMPTY
    return EXIT_INVALID_QUERY


def main() -> None:
    try:
        app()
    except Clamp3SidecarError as exc:
        console.print(f"[FAIL] {exc}")
        raise typer.Exit(EXIT_BACKEND_UNAVAILABLE) from exc
    except FileNotFoundError as exc:
        console.print(f"[FAIL] source file not found: {exc}")
        raise typer.Exit(EXIT_SOURCE_ERROR) from exc
    except ValueError as exc:
        console.print(f"[FAIL] {exc}")
        raise typer.Exit(_map_value_error(exc)) from exc
    except KeyboardInterrupt as exc:
        console.print("[STOP] interrupted; completed SQLite writes are preserved")
        raise typer.Exit(EXIT_INTERRUPTED) from exc
    except RuntimeError as exc:
        console.print(f"[FAIL] {exc}")
        raise typer.Exit(EXIT_INTERNAL_ERROR) from exc


if __name__ == "__main__":
    main()
