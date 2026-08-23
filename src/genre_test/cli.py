from __future__ import annotations

import platform
from pathlib import Path

import torch
import typer
from rich.console import Console
from rich.table import Table

from .analyzer import ANALYSIS_MODES, GenreAnalyzer
from .audio import iter_audio_files
from .maest import DEFAULT_MODEL
from .models import AnalysisResult
from .report import write_json, write_summary_csv

app = typer.Typer(no_args_is_help=True, help="Local music genre analyzer")
console = Console()


def _print_result(result: AnalysisResult) -> None:
    console.print(f"\n[bold]{Path(result.path).name}[/bold]")
    console.print(
        f"Resolved: [bold cyan]{result.resolved_genre or result.primary_genre}[/bold cyan] | "
        f"Family: {result.primary_genre} ({(result.primary_genre_score or 0.0):.3f}) | "
        f"{result.classification}, confidence={result.confidence} | "
        f"mode={result.analysis_mode}, windows={result.windows_analyzed} | "
        f"BPM: {result.audio_features.bpm} | "
        f"Key: {result.audio_features.key} {result.audio_features.mode or ''}"
    )
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
        raise typer.BadParameter(f"mode must be one of: {', '.join(sorted(ANALYSIS_MODES))}")
    return GenreAnalyzer(
        model_id=model,
        revision=revision,
        device=device,
        analysis_mode=normalized_mode,
        window_count=windows,
        top_k=top_k,
    )


@app.command()
def doctor() -> None:
    """Show runtime and CUDA status."""
    console.print(f"Python: {platform.python_version()}")
    console.print(f"Platform: {platform.platform()}")
    console.print(f"Torch: {torch.__version__}")
    console.print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        console.print(f"CUDA runtime: {torch.version.cuda}")
        console.print(f"GPU: {torch.cuda.get_device_name(0)}")


@app.command()
def analyze(
    audio: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    out: Path = typer.Option(Path("results"), help="Output directory"),
    model: str = typer.Option(DEFAULT_MODEL, help="Hugging Face model id"),
    revision: str | None = typer.Option(None, help="Optional fixed model revision/commit"),
    device: str = typer.Option("auto", help="auto|cpu|cuda"),
    mode: str = typer.Option("auto", help="auto|fast|accurate|expert"),
    windows: int = typer.Option(5, min=1, max=12, help="Expert mode only"),
    top_k: int = typer.Option(15, min=3, max=50, help="Reported detailed styles"),
) -> None:
    """Analyze one audio file."""
    analyzer = _make_analyzer(model, revision, device, mode, windows, top_k)
    result = analyzer.analyze(audio)
    target = write_json(result, out)
    _print_result(result)
    console.print(f"JSON: {target}")


@app.command()
def batch(
    source: Path = typer.Argument(..., exists=True, readable=True),
    out: Path = typer.Option(Path("results"), help="Output directory"),
    model: str = typer.Option(DEFAULT_MODEL, help="Hugging Face model id"),
    revision: str | None = typer.Option(None, help="Optional fixed model revision/commit"),
    device: str = typer.Option("auto", help="auto|cpu|cuda"),
    mode: str = typer.Option("auto", help="auto|fast|accurate|expert"),
    windows: int = typer.Option(5, min=1, max=12, help="Expert mode only"),
    top_k: int = typer.Option(15, min=3, max=50, help="Reported detailed styles"),
) -> None:
    """Analyze all supported audio files in a directory recursively."""
    files = iter_audio_files(source)
    if not files:
        raise typer.BadParameter("No supported audio files found")

    analyzer = _make_analyzer(model, revision, device, mode, windows, top_k)
    results: list[AnalysisResult] = []
    for idx, path in enumerate(files, 1):
        console.rule(f"[{idx}/{len(files)}] {path.name}")
        result = analyzer.analyze(path)
        results.append(result)
        write_json(result, out)
        _print_result(result)

    csv_path = write_summary_csv(results, out)
    console.print(f"\nSummary: {csv_path}")


if __name__ == "__main__":
    app()
