from __future__ import annotations

import platform
from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console

from . import __version__
from .model_config import (
    DEFAULT_CUDA_BATCH_SIZE,
    DEFAULT_MODEL,
    DEFAULT_MODEL_REVISION,
    DEFAULT_SEMANTIC_MODEL,
    DEFAULT_SEMANTIC_MODEL_REVISION,
)

if TYPE_CHECKING:
    from .models import AnalysisResult
    from .profile_analyzer import ProfileAnalyzer

app = typer.Typer(
    no_args_is_help=True,
    help="Local ensemble music analyzer and validation lab",
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


def _print_result(result: AnalysisResult, view: str = "normal") -> None:
    from .presentation import format_result_text

    console.print()
    console.print(format_result_text(result, view=view))


def _make_analyzer(
    model: str,
    revision: str | None,
    device: str,
    mode: str,
    windows: int,
    top_k: int,
    semantic_mode: str,
) -> ProfileAnalyzer:
    from .analysis_policy import ANALYSIS_MODES
    from .profile_analyzer import SEMANTIC_MODES, ProfileAnalyzer

    normalized_mode = mode.lower().strip()
    if normalized_mode not in ANALYSIS_MODES:
        raise typer.BadParameter(
            f"mode must be one of: {', '.join(sorted(ANALYSIS_MODES))}"
        )
    normalized_semantic = semantic_mode.lower().strip()
    if normalized_semantic not in SEMANTIC_MODES:
        raise typer.BadParameter("semantic must be auto, on or off")
    return ProfileAnalyzer(
        model_id=model,
        revision=revision,
        device=device,
        analysis_mode=normalized_mode,
        window_count=windows,
        top_k=top_k,
        semantic_mode=normalized_semantic,
    )


def _store_result(
    result: AnalysisResult,
    out: Path,
    history_db: Path | None,
    no_history: bool,
) -> Path:
    from .history import HistoryDB
    from .report import write_json

    target = write_json(result, out)
    if not no_history:
        HistoryDB(history_db).record_result(result)
    return target


@app.command()
def doctor() -> None:
    """Show runtime, decoder, authentication and pinned model/CUDA status."""
    import soundfile as sf
    import torch

    from .runtime_diagnostics import collect_runtime_diagnostics
    from .runtime_meta import default_history_path

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
    console.print(f"Default AudioSet AST: {DEFAULT_SEMANTIC_MODEL}")
    console.print(f"Pinned AudioSet AST revision: {DEFAULT_SEMANTIC_MODEL_REVISION}")
    console.print(f"Default CUDA MAEST batch: up to {DEFAULT_CUDA_BATCH_SIZE} windows")
    console.print("Semantic profile: 3 x 10 s AudioSet windows, one batched AST pass")
    console.print(f"History DB: {default_history_path()}")


@app.command()
def analyze(
    audio: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    out: Path = typer.Option(Path("results"), help="Output directory"),
    model: str = typer.Option(DEFAULT_MODEL, help="Hugging Face MAEST model id"),
    revision: str | None = typer.Option(
        None,
        help="Optional fixed MAEST revision/commit; default MAEST is pinned automatically",
    ),
    device: str = typer.Option("auto", help="auto|cpu|cuda"),
    mode: str = typer.Option("auto", help="auto|fast|accurate|expert"),
    semantic: str = typer.Option(
        "auto",
        help="AudioSet semantic layer: auto|on|off; auto falls back to MAEST-only on failure",
    ),
    view: str = typer.Option("normal", help="normal|suno|distributor"),
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
    """Analyze one audio file and store an ensemble AudioProfile snapshot."""
    if view not in {"normal", "suno", "distributor"}:
        raise typer.BadParameter("view must be normal, suno or distributor")
    analyzer = _make_analyzer(model, revision, device, mode, windows, top_k, semantic)
    result = analyzer.analyze(audio)
    target = _store_result(result, out, history_db, no_history)
    _print_result(result, view)
    console.print(f"JSON: {target}")


@app.command()
def batch(
    source: Path = typer.Argument(..., exists=True, readable=True),
    out: Path = typer.Option(Path("results"), help="Output directory"),
    model: str = typer.Option(DEFAULT_MODEL, help="Hugging Face MAEST model id"),
    revision: str | None = typer.Option(
        None,
        help="Optional fixed MAEST revision/commit",
    ),
    device: str = typer.Option("auto", help="auto|cpu|cuda"),
    mode: str = typer.Option("auto", help="auto|fast|accurate|expert"),
    semantic: str = typer.Option(
        "auto",
        help="AudioSet semantic layer: auto|on|off",
    ),
    view: str = typer.Option("normal", help="normal|suno|distributor"),
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
    from .audio import iter_audio_files
    from .history import HistoryDB
    from .report import write_json, write_summary_csv

    if view not in {"normal", "suno", "distributor"}:
        raise typer.BadParameter("view must be normal, suno or distributor")
    files = iter_audio_files(source, include_service_dirs=include_service_dirs)
    if not files:
        raise typer.BadParameter("No supported audio files found")

    analyzer = _make_analyzer(model, revision, device, mode, windows, top_k, semantic)
    history = None if no_history else HistoryDB(history_db)
    results: list[AnalysisResult] = []
    for idx, path in enumerate(files, 1):
        console.rule(f"[{idx}/{len(files)}] {path.name}")
        result = analyzer.analyze(path)
        results.append(result)
        target = write_json(result, out)
        if history:
            history.record_result(result)
        _print_result(result, view)
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
        help="Run Fast + Auto + Accurate from one shared MAEST prediction cache",
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
    """Recheck raw MAEST convergence/history without changing the 0.3 validation baseline."""
    from .analysis_policy import ANALYSIS_MODES
    from .validation import ValidationEngine, format_validation_session
    from .validation_policy import RECHECK_FILTERS

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
    from .validation import ValidationEngine

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
    """Compare latest stored raw MAEST results for two analyzer versions."""
    from .analysis_policy import ANALYSIS_MODES
    from .validation import ValidationEngine, format_version_comparison

    if mode not in ANALYSIS_MODES | {"any"}:
        raise typer.BadParameter("mode must be auto, fast, accurate, expert or any")
    engine = ValidationEngine(history_path=history_db, out_dir=out)
    result = engine.compare_versions(version_a, version_b, mode=mode)
    console.print(format_version_comparison(result))


if __name__ == "__main__":
    app()
