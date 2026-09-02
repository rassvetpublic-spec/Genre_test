from __future__ import annotations

import pytest

from genre_test.workstation.server import main


def test_workstation_entrypoint_rejects_non_loopback_host(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--host", "0.0.0.0", "--port", "0", "--quiet"]) == 2
    captured = capsys.readouterr()
    assert "loopback" in captured.err


def test_workstation_entrypoint_rejects_invalid_port(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--host", "127.0.0.1", "--port", "70000", "--quiet"]) == 2
    captured = capsys.readouterr()
    assert "port must be between 0 and 65535" in captured.err
