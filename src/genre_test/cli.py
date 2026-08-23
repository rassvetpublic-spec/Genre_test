from __future__ import annotations

import platform
from pathlib import Path

import soundfile as sf
import torch
import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .analysis_policy import ANALYSIS_MODES
from .analyzer import GenreAnalyzer
from .audio import iter_audio_files
from .history import HistoryDB
from .maest import DEFAULT_CUDA_BATCH_SIZE, DEFAULT_MODEL, DEFAULT_MODEL_REVISION
from .models import AnalysisResult
from .report import write_json, write_summary_csv
from .runtime_diagnostics import collect_runtime_diagnostics
from .runtime_meta import default_history_path
from .validation import (
    ValidationEngine,
    format_validation_session,
    format_version_comparison,
)
from .validation_policy import RECHECK_FILTERS

app = typer.Typer(
    no_args_is_help=True,
    help="Local music genre analyzer and validation lab",
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"Genre_test {__version__}")
        raise typer.Exit()


@app.callback()
def root_callback(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show Genre_test version and exit",
    ),
) -> None:
    """Genre_test command line interface."""
    del version


def _print_result(result: AnalysisResult) -> None:
    console.print(f"\n[bold]{Path(result.path).name}[/bold]")
    console.print(
        f"Resolved: [bold cyan]{result.resolved_genre or result.primary_genre}[/bold cyan] | "
        f"Family: {result.primary_genre} ({(result.primary_genre_score or 0.0):.3f}) | "
        f"{result.classification}, confidence={result.confidence} | "
        f"quality={result.input_quality} | "
        f"mode={result.analysis_mode}, windows={result.windows_analyzed} | "
        f"BPM: {result.audio_features.bpm} | "
        f"Key: {result.audio_features.key} {result.audio_features.mode or ''}"
    )
    console.print(
        f"Version: {result.analyzer_version} | schema={result.schema_version} | "
        f"MAEST revision={result.model_revision or 'un-pinned'}"
    )
    console.print(f"run={result.run_id} | track={result.track_id}")
    if result.quality_notes:
        console.print("QC: " + "; ".join(result.quality_notes))
    table = Table("#", "Style", "Score")
    for idx, item in enumerate(result.top_styles[:10], 1):
        table.add_row(str(idx), item.label, f"{item.score:.4f}")
    console.print(table)


def _make_analyzer(
    model: str,
    revision: str | None,
    device: str,
    mode: str,
    windows: int,
    top_k: int,
) -> GenreAnalyzer:
    normalized_mode = mode.lower().strip()
    if normalized_mode not in ANALYSIS_MODES:
        raise typer.BadParameter(
            f"mode must be one of: {', '.join(sorted(ANALYSIS_MODES))}"
        )
    return GenreAnalyzer(
        model_id=model,
        revision=revision,
        device=device,
        analysis_mode=normalized_mode,
        window_count=windows,
        top_k=top_k,
    )


def _store_result(
    result: AnalysisResult,
    out: Path,
    history_db: Path | None,
    no_history: bool,
) -> Path:
    target = write_json(result, out)
    if not no_history:
        HistoryDB(history_db).record_result(result)
    return target


@app.command()
def doctor() -> None:
    """Show runtime, decoder, authentication, pinned model and CUDA status."""
    diagnostics = collect_runtime_diagnostics()
    console.print(f"Genre_test: {__version__}")
    console.print(f"Python: {platform.python_version()}")
    console.print(f"Platform: {platform.platform()}")
    console.print(f"Torch: {torch.__version__}")
    console.print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        console.print(f"CUDA runtime: {torch.version.cuda}")
        console.print(f"GPU: {torch.cuda.get_device_name(0)}")
    console.print(f"SoundFile: {sf.__version__}")
    if diagnostics.ffmpeg_available:
        console.print(f"FFmpeg: {diagnostics.ffmpeg_path}")
        console.print("AAC/extended decode fallback: available via FFmpeg")
    else:
        console.print("[bold red]FFmpeg: MISSING[/bold red]")
        console.print(
            "[bold red]AAC/extended decode fallback: unavailable without FFmpeg[/bold red]"
        )
    console.print(f"HF authentication: {diagnostics.hf_auth_label}")
    console.print(f"Default MAEST: {DEFAULT_MODEL}")
    console.print(f"Pinned MAEST revision: {DEFAULT_MODEL_REVISION}")
    console.print(f"Default CUDA inference batch: up to {DEFAULT_CUDA_BATCH_SIZE} windows")
    console.print(f"History DB: {default_history_path()}")


@app.command()
def analyze(
    audio: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    out: Path = typer.Option(Path("results"), help="Output directory"),
    model: str = typer.Option(DEFAULT_MODEL, help="Hugging Face model id"),
    revision: str | None = typer.Option(
        None,
        help="Optional fixed model revision/commit; default MAEST is pinned automatically",
    ),
    device: str = typer.Option("auto", help="auto|cpu|cuda"),
    mode: str = typer.Option("auto", help="auto|fast|accurate|expert"),
    windows: int = typer.Option(5, min=1, max=12, help="Expert mode only"),
    top_k: int = typer.Option(15, min=3, max=50, help="Reported detailed styles"),
    history_db: Path | None = typer.Option(
        None,
        help="Override history SQLite path",
    ),
    no_history: bool = typer.Option(
        False,
        "--no-history",
        help="Do not store this run in history",
    ),
) -> None:
    """Analyze one audio file and store a versioned snapshot."""
    analyzer = _make_analyzer(model, revision, device, mode, windows, top_k)
    result = analyzer.analyze(audio)
    target = _store_result(result, out, history_db, no_history)
    _print_result(result)
    console.print(f"JSON: {target}")


@app.command()
def batch(
    source: Path = typer.Argument(..., exists=True, readable=True),
    out: Path = typer.Option(Path("results"), help="Output directory"),
    model: str = typer.Option(DEFAULT_MODEL, help="Hugging Face model id"),
    revision: str | None = typer.Option(
        None,
        help="Optional fixed model revision/commit",
    ),
    device: str = typer.Option("auto", help="auto|cpu|cuda"),
    mode: str = typer.Option("auto", help="auto|fast|accurate|expert"),
    windows: int = typer.Option(5, min=1, max=12, help="Expert mode only"),
    top_k: int = typer.Option(15, min=3, max=50, help="Reported detailed styles"),
    history_db: Path | None = typer.Option(
        None,
        help="Override history SQLite path",
    ),
    no_history: bool = typer.Option(
        False,
        "--no-history",
        help="Do not store runs in history",
    ),
    include_service_dirs: bool = typer.Option(
        False,
        "--include-service-dirs",
        help="Also scan .git/.venv/.genre_test/results/Resources/audioAlg",
    ),
) -> None:
    """Analyze all supported audio files in a directory recursively."""
    files = iter_audio_files(source, include_service_dirs=include_service_dirs)
    if not files:
        raise typer.BadParameter("No supported audio files found")

    analyzer = _make_analyzer(model, revision, device, mode, windows, top_k)
    history = None if no_history else HistoryDB(history_db)
    results: list[AnalysisResult] = []
    for idx, path in enumerate(files, 1):
        console.rule(f"[{idx}/{len(files)}] {path.name}")
        result = analyzer.analyze(path)
        results.append(result)
        target = write_json(result, out)
        if history:
            history.record_result(result)
        _print_result(result)
        console.print(f"JSON: {target}")

    csv_path = write_summary_csv(results, out)
    console.print(f"\nSummary: {csv_path}")


@app.command("validate")
def validate_command(
    sources: list[Path] = typer.Argument(..., exists=True, readable=True),
    out: Path = typer.Option(
        Path("results") / "validation",
        help="Validation report directory",
    ),
    history_db: Path | None = typer.Option(
        None,
        help="Override history SQLite path",
    ),
    device: str = typer.Option("auto", help="auto|cpu|cuda"),
    mode: str = typer.Option(
        "auto",
        help="Mode used when --compare-modes is off",
    ),
    compare_modes: bool = typer.Option(
        False,
        "--compare-modes",
        help="Run Fast + Auto + Accurate from one shared prediction cache",
    ),
    filter_mode: str = typer.Option(
        "all",
        "--filter",
        help="all|old_versions|unstable",
    ),
    import_json: bool = typer.Option(
        False,
        "--import-json",
        help="Import existing *.genre*.json under the sources first",
    ),
    include_service_dirs: bool = typer.Option(
        False,
        "--include-service-dirs",
        help="Include normally ignored service/cache audio directories",
    ),
) -> None:
    """Recheck scattered tracks, compare modes and automatically analyze drift."""
    if filter_mode not in RECHECK_FILTERS:
        raise typer.BadParameter(
            f"filter must be one of: {', '.join(sorted(RECHECK_FILTERS))}"
        )
    if mode not in ANALYSIS_MODES - {"expert"}:
        raise typer.BadParameter("validation mode must be auto, fast or accurate")
    engine = ValidationEngine(
        history_path=history_db,
        out_dir=out,
        device=device,
        include_service_dirs=include_service_dirs,
    )
    if import_json:
        imported, skipped = engine.import_history_sources(sources)
        console.print(f"Imported historical JSON: {imported}; skipped: {skipped}")

    def progress(current: int, total: int, message: str) -> None:
        console.print(f"[{current}/{total}] {message}")

    result = engine.recheck(
        sources,
        mode=mode,
        compare_all_modes=compare_modes,
        filter_mode=filter_mode,
        progress=progress,
    )
    console.print(format_validation_session(result))


@app.command("history-import")
def history_import_command(
    sources: list[Path] = typer.Argument(..., exists=True, readable=True),
    history_db: Path | None = typer.Option(
        None,
        help="Override history SQLite path",
    ),
) -> None:
    """Import legacy/current *.genre*.json snapshots into central history."""
    engine = ValidationEngine(history_path=history_db)
    imported, skipped = engine.import_history_sources(sources)
    console.print(f"Imported: {imported}; skipped/unmatched: {skipped}")
    console.print(f"History DB: {engine.history.path}")


@app.command("compare-versions")
def compare_versions_command(
    version_a: str = typer.Argument(...),
    version_b: str = typer.Argument(...),
    mode: str = typer.Option(
        "auto",
        help="auto|fast|accurate|expert|any; 'any' is diagnostic and may compare different modes",
    ),
    out: Path = typer.Option(
        Path("results") / "validation",
        help="Report directory",
    ),
    history_db: Path | None = typer.Option(
        None,
        help="Override history SQLite path",
    ),
) -> None:
    """Compare latest stored results for two analyzer versions."""
    if mode not in ANALYSIS_MODES | {"any"}:
        raise typer.BadParameter(
            "mode must be auto, fast, accurate, expert or any"
        )
    engine = ValidationEngine(history_path=history_db, out_dir=out)
    result = engine.compare_versions(version_a, version_b, mode=mode)
    console.print(format_version_comparison(result))


if __name__ == "__main__":
    app()
