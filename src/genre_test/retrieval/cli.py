from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from ..runtime_meta import default_history_path, default_state_dir, project_root
from .clamp3_sidecar_backend import Clamp3SidecarBackend, default_clamp3_backend_info
from .contracts import SearchFilter
from .export import write_search_csv, write_search_json
from .service import index_catalog, index_status, rebuild_catalog, search_audio, search_text
from .storage import RetrievalStore

app = typer.Typer(
    no_args_is_help=True,
    help="Genre_test v0.5 local CLaMP retrieval catalog and exact-search tools",
)
console = Console()


def _default_db() -> Path:
    return default_state_dir() / "retrieval.sqlite3"


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


def _export(result: object, *, json_out: Path | None, csv_out: Path | None) -> None:
    if json_out is not None:
        target = write_search_json(result, json_out)  # type: ignore[arg-type]
        console.print(f"JSON: {target}")
    if csv_out is not None:
        target = write_search_csv(result, csv_out)  # type: ignore[arg-type]
        console.print(f"CSV: {target}")


@app.command("status")
def status_command(
    db: Annotated[Path | None, typer.Option("--db", help="Retrieval SQLite path")] = None,
    history: Annotated[Path | None, typer.Option("--history", help="Analysis history SQLite path")] = None,
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


@app.command("index")
def index_command(
    db: Annotated[Path | None, typer.Option("--db")] = None,
    history: Annotated[Path | None, typer.Option("--history")] = None,
    limit: Annotated[
        int | None,
        typer.Option("--limit", min=1, help="Pilot: process only first N catalog tracks"),
    ] = None,
) -> None:
    """Incrementally index missing/current-stale tracks; completed rows are resumable cache hits."""
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
    instrument: Annotated[str | None, typer.Option("--instrument", help="Comma-separated")] = None,
    production: Annotated[str | None, typer.Option("--production", help="Comma-separated")] = None,
    source_folder: Annotated[str | None, typer.Option("--source-folder", help="Comma-separated roots")] = None,
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
    instrument: Annotated[str | None, typer.Option("--instrument", help="Comma-separated")] = None,
    production: Annotated[str | None, typer.Option("--production", help="Comma-separated")] = None,
    source_folder: Annotated[str | None, typer.Option("--source-folder", help="Comma-separated roots")] = None,
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


@app.command("history")
def history_command(
    db: Annotated[Path | None, typer.Option("--db")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=1000)] = 50,
) -> None:
    """Show local retrieval-query history stored separately from analysis history."""
    records = RetrievalStore(db or _default_db()).search_history(limit=limit)
    _print_json(
        [
            {
                "query_id": record.query_id,
                "query_type": record.query_type,
                "backend_fingerprint": record.backend_fingerprint,
                "query_text": record.query_text,
                "language": record.language,
                "query_track_id": record.query_track_id,
                "top_k": record.top_k,
                "filters": record.filters,
                "embedding_seconds": record.embedding_seconds,
                "ranking_seconds": record.ranking_seconds,
                "result_count": record.result_count,
                "created_at": record.created_at,
            }
            for record in records
        ]
    )


if __name__ == "__main__":
    app()
