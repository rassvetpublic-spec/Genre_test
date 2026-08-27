from pathlib import Path

from typer.testing import CliRunner

from genre_test.retrieval.cli import app

ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()


def test_retrieval_cli_help_is_lightweight() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0, result.output
    for command in ("status", "index", "rebuild", "search-audio", "search-text", "history"):
        assert command in result.output


def test_root_launcher_aliases_are_registered_in_cli() -> None:
    for command in (
        "retrieval-index-status",
        "retrieval-index",
        "retrieval-rebuild",
        "retrieval-search-audio",
        "retrieval-search-text",
        "retrieval-search-history",
    ):
        result = runner.invoke(app, [command, "--help"])
        assert result.exit_code == 0, f"{command}: {result.output}"


def test_root_launcher_forwards_product_commands_without_internal_scripts() -> None:
    launcher = (ROOT / "Genre_test_START.cmd").read_text(encoding="utf-8")
    assert 'if /I "%~1"=="retrieval-index" goto WORKING_RETRIEVAL_PRODUCT' in launcher
    assert 'if /I "%~1"=="retrieval-index-status" goto WORKING_RETRIEVAL_PRODUCT' in launcher
    assert 'if /I "%~1"=="retrieval-search-text" goto WORKING_RETRIEVAL_PRODUCT' in launcher
    assert 'if /I "%~1"=="retrieval-search-audio" goto WORKING_RETRIEVAL_PRODUCT' in launcher
    assert '"%ROOT%.venv\\Scripts\\genre-test-retrieval.exe" %*' in launcher
    assert 'if not exist "%ROOT%.venv\\Scripts\\genre-test-retrieval.exe" set "NEED_SETUP=1"' in launcher
