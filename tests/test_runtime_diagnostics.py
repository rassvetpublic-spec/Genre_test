from __future__ import annotations

from genre_test import runtime_diagnostics


def test_ffmpeg_warning_when_missing(monkeypatch) -> None:
    monkeypatch.setattr(runtime_diagnostics.shutil, "which", lambda _name: None)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.delenv("USERPROFILE", raising=False)
    monkeypatch.delenv("ProgramData", raising=False)
    monkeypatch.delenv("ProgramFiles", raising=False)
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


def test_find_ffmpeg_uses_winget_links_and_updates_process_path(tmp_path, monkeypatch) -> None:
    local_app_data = tmp_path / "LocalAppData"
    ffmpeg = local_app_data / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe"
    ffmpeg.parent.mkdir(parents=True)
    ffmpeg.write_bytes(b"fake")

    monkeypatch.setattr(runtime_diagnostics.shutil, "which", lambda _name: None)
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.delenv("USERPROFILE", raising=False)
    monkeypatch.delenv("ProgramData", raising=False)
    monkeypatch.delenv("ProgramFiles", raising=False)
    monkeypatch.setenv("PATH", "")

    discovered = runtime_diagnostics.find_ffmpeg()

    assert discovered == str(ffmpeg.resolve())
    path_entries = runtime_diagnostics.os.environ["PATH"].split(runtime_diagnostics.os.pathsep)
    assert str(ffmpeg.parent.resolve()) in path_entries
