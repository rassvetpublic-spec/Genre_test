from __future__ import annotations

from inspect import signature

from genre_test.cli import analyze, batch


def _assert_v04_defaults(command) -> None:
    params = signature(command).parameters
    assert params["view"].default.default == "all"
    assert params["full_path"].default.default is False


def test_v04_analyze_defaults_to_all_views_and_short_paths() -> None:
    _assert_v04_defaults(analyze)


def test_v04_batch_defaults_to_all_views_and_short_paths() -> None:
    _assert_v04_defaults(batch)
