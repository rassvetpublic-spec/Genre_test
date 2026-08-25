from __future__ import annotations

from click import Command
from typer.main import get_command

from genre_test.cli import app


def _subcommand(name: str) -> Command:
    root = get_command(app)
    command = root.commands.get(name)
    assert command is not None
    return command


def _param(command: Command, name: str):
    for param in command.params:
        if param.name == name:
            return param
    raise AssertionError(f"Missing CLI parameter: {name}")


def test_v04_analyze_defaults_to_all_views_and_short_paths() -> None:
    command = _subcommand("analyze")
    view = _param(command, "view")
    full_path = _param(command, "full_path")

    assert view.default == "all"
    assert full_path.default is False
    assert "--full-path" in full_path.opts


def test_v04_batch_defaults_to_all_views_and_short_paths() -> None:
    command = _subcommand("batch")
    view = _param(command, "view")
    full_path = _param(command, "full_path")

    assert view.default == "all"
    assert full_path.default is False
    assert "--full-path" in full_path.opts
