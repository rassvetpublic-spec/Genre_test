from pathlib import Path

from typer.testing import CliRunner

from genre_test.retrieval.cli import app
from genre_test.retrieval.entrypoint import _ALIAS_MAP

ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()


def test_retrieval_cli_help_is_lightweight() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0, result.output
    for command in (
        "status",
        "index",
        "rebuild",
        "search-audio",
        "search-text",
        "history",
        "segment-status",
        "segment-index",
        "search-representative",
        "search-segment",
        "catalog-audit",
        "retry-missing",
        "benchmark-run",
        "exit-codes",
    ):
        assert command in result.output


def test_existing_root_launcher_aliases_are_registered_in_cli() -> None:
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


def test_new_root_launcher_aliases_have_explicit_entrypoint_mapping() -> None:
    assert _ALIAS_MAP == {
        "retrieval-segment-status": "segment-status",
        "retrieval-segment-index": "segment-index",
        "retrieval-search-representative": "search-representative",
        "retrieval-search-segment": "search-segment",
        "retrieval-catalog-audit": "catalog-audit",
        "retrieval-retry-missing": "retry-missing",
        "retrieval-benchmark-run": "benchmark-run",
        "retrieval-exit-codes": "exit-codes",
    }


def test_root_launcher_forwards_product_commands_without_internal_scripts() -> None:
    launcher = (ROOT / "Genre_test_START.cmd").read_text(encoding="utf-8")
    for command in (
        "retrieval-index",
        "retrieval-index-status",
        "retrieval-search-text",
        "retrieval-search-audio",
        "retrieval-segment-status",
        "retrieval-segment-index",
        "retrieval-search-representative",
        "retrieval-search-segment",
        "retrieval-catalog-audit",
        "retrieval-retry-missing",
        "retrieval-benchmark-run",
        "retrieval-exit-codes",
    ):
        assert f'if /I "%~1"=="{command}" goto WORKING_RETRIEVAL_PRODUCT' in launcher
    assert '"%ROOT%.venv\\Scripts\\genre-test-retrieval.exe" %*' in launcher
    assert 'if not exist "%ROOT%.venv\\Scripts\\genre-test-retrieval.exe" set "NEED_SETUP=1"' in launcher


def test_exit_code_contract_is_machine_readable() -> None:
    result = runner.invoke(app, ["exit-codes"])
    assert result.exit_code == 0, result.output
    for pair in (
        '"success": 0',
        '"backend_unavailable": 20',
        '"index_empty_or_required_embedding_missing": 21',
        '"invalid_query_or_arguments": 22',
        '"source_file_error": 23',
        '"internal_error": 70',
        '"interrupted_safe_stop": 130',
    ):
        assert pair in result.output
