from __future__ import annotations

from genre_test import runtime_diagnostics


def test_ffmpeg_warning_when_missing(monkeypatch) -> None:
    monkeypatch.setattr(runtime_diagnostics.shutil, "which", lambda _name: None)
    monkeypatch.setenv("HF_TOKEN", "test-token")
    diagnostics = runtime_diagnostics.collect_runtime_diagnostics()
    assert diagnostics.ffmpeg_available is False
    assert diagnostics.decoder_warning is not None
    assert "FFmpeg" in diagnostics.decoder_warning
    assert diagnostics.hf_token_available is True
    assert diagnostics.hf_auth_source == "HF_TOKEN"


def test_ffmpeg_present(monkeypatch) -> None:
    monkeypatch.setattr(runtime_diagnostics.shutil, "which", lambda _name: "/usr/bin/ffmpeg")
    monkeypatch.setenv("HF_TOKEN", "test-token")
    diagnostics = runtime_diagnostics.collect_runtime_diagnostics()
    assert diagnostics.ffmpeg_available is True
    assert diagnostics.decoder_warning is None
