from __future__ import annotations

from types import SimpleNamespace

import pytest

from genre_test import runtime_health
from genre_test.runtime_health import RuntimeComponent, RuntimeHealth


def test_compact_summary_reports_key_capabilities() -> None:
    health = RuntimeHealth(
        (
            RuntimeComponent("NumPy", "OK", "2.5.2", category="Package"),
            RuntimeComponent("PyTorch", "OK", "2.11.0", category="Package"),
            RuntimeComponent("CUDA", "OK", "12.8", category="Acceleration"),
            RuntimeComponent("FFmpeg", "OK", "ffmpeg.exe", category="External"),
            RuntimeComponent("HF auth", "WARN", "anonymous", category="External"),
        )
    )

    assert health.overall_status == "WARN"
    assert health.package_ok_count == 2
    assert health.package_count == 2
    assert health.compact_summary == "Deps: 2/2 | CUDA: OK | FFmpeg: OK | HF: WARN"


def test_collect_runtime_health_detects_missing_package(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_version(name: str) -> str:
        if name == "transformers":
            raise runtime_health.PackageNotFoundError
        return "1.0.0"

    fake_cuda = SimpleNamespace(
        is_available=lambda: True,
        get_device_name=lambda _index: "Test GPU",
    )
    fake_torch = SimpleNamespace(cuda=fake_cuda, version=SimpleNamespace(cuda="12.8"))
    fake_diagnostics = SimpleNamespace(
        ffmpeg_available=True,
        ffmpeg_path="C:/ffmpeg.exe",
        hf_token_available=True,
        hf_auth_label="token available (test)",
    )

    monkeypatch.setattr(runtime_health, "package_version", fake_version)
    monkeypatch.setattr(runtime_health.importlib, "import_module", lambda _name: fake_torch)
    monkeypatch.setattr(runtime_health, "collect_runtime_diagnostics", lambda: fake_diagnostics)

    health = runtime_health.collect_runtime_health()

    transformers = health.by_name("Transformers")
    assert transformers is not None
    assert transformers.status == "FAIL"
    assert transformers.value == "MISSING"
    assert health.overall_status == "FAIL"


def test_collect_runtime_health_marks_cpu_fallback_as_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_cuda = SimpleNamespace(is_available=lambda: False)
    fake_torch = SimpleNamespace(cuda=fake_cuda, version=SimpleNamespace(cuda=None))
    fake_diagnostics = SimpleNamespace(
        ffmpeg_available=True,
        ffmpeg_path="C:/ffmpeg.exe",
        hf_token_available=True,
        hf_auth_label="token available (test)",
    )

    monkeypatch.setattr(runtime_health, "package_version", lambda _name: "1.0.0")
    monkeypatch.setattr(runtime_health.importlib, "import_module", lambda _name: fake_torch)
    monkeypatch.setattr(runtime_health, "collect_runtime_diagnostics", lambda: fake_diagnostics)

    health = runtime_health.collect_runtime_health()

    assert health.by_name("CUDA").status == "WARN"  # type: ignore[union-attr]
    assert health.by_name("GPU").value == "CPU mode"  # type: ignore[union-attr]
    assert health.overall_status == "WARN"
