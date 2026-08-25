from __future__ import annotations

from types import SimpleNamespace

import pytest

from genre_test import runtime_health
from genre_test.runtime_health import RuntimeComponent, RuntimeHealth


def test_compact_summary_reports_key_capabilities() -> None:
    health = RuntimeHealth(
        (
            RuntimeComponent("NumPy", "OK", "2.5.2", category="Package"),
            RuntimeComponent("PyTorch", "OK", "2.12.1", category="Package"),
            RuntimeComponent("CUDA", "OK", "13.0", category="Acceleration"),
            RuntimeComponent(
                "GPU architecture",
                "OK",
                "Blackwell native (sm_120)",
                category="Acceleration",
            ),
            RuntimeComponent("FFmpeg", "OK", "ffmpeg.exe", category="External"),
            RuntimeComponent("HF auth", "WARN", "anonymous", category="External"),
        )
    )

    assert health.overall_status == "WARN"
    assert health.package_ok_count == 2
    assert health.package_count == 2
    assert health.compact_summary == (
        "Deps: 2/2 | CUDA: OK | GPU: OK | FFmpeg: OK | HF: WARN"
    )


@pytest.mark.parametrize(
    ("version_info", "expected_status"),
    [
        ((3, 11, 0), "OK"),
        ((3, 12, 0), "OK"),
        ((3, 13, 0), "OK"),
        ((3, 14, 0), "FAIL"),
    ],
)
def test_python_component_supports_311_through_313(
    monkeypatch: pytest.MonkeyPatch,
    version_info: tuple[int, int, int],
    expected_status: str,
) -> None:
    monkeypatch.setattr(runtime_health.sys, "version_info", version_info)

    component = runtime_health._python_component()

    assert component.status == expected_status
    assert component.details == "Supported: >=3.11,<3.14"


def _blackwell_cuda(*, native: bool = True, cuda_version: str = "13.0") -> SimpleNamespace:
    arches = ["sm_75", "sm_80", "sm_86", "sm_90", "sm_100"]
    if native:
        arches.append("sm_120")
    return SimpleNamespace(
        is_available=lambda: True,
        get_device_name=lambda _index: "NVIDIA GeForce RTX 5070 Ti",
        get_device_capability=lambda _index: (12, 0),
        get_arch_list=lambda: arches,
        _test_cuda_version=cuda_version,
    )


def _diagnostics() -> SimpleNamespace:
    return SimpleNamespace(
        ffmpeg_available=True,
        ffmpeg_path="C:/ffmpeg.exe",
        hf_token_available=True,
        hf_auth_label="token available (test)",
    )


def test_collect_runtime_health_detects_missing_package(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_version(name: str) -> str:
        if name == "transformers":
            raise runtime_health.PackageNotFoundError
        return "1.0.0"

    fake_cuda = _blackwell_cuda()
    fake_torch = SimpleNamespace(
        __version__="2.12.1+cu130",
        cuda=fake_cuda,
        version=SimpleNamespace(cuda="13.0"),
    )

    monkeypatch.setattr(runtime_health, "package_version", fake_version)
    monkeypatch.setattr(runtime_health.importlib, "import_module", lambda _name: fake_torch)
    monkeypatch.setattr(runtime_health, "collect_runtime_diagnostics", _diagnostics)

    health = runtime_health.collect_runtime_health()

    transformers = health.by_name("Transformers")
    assert transformers is not None
    assert transformers.status == "FAIL"
    assert transformers.value == "MISSING"
    assert health.by_name("CUDA").status == "OK"  # type: ignore[union-attr]
    assert health.by_name("GPU architecture").value == (  # type: ignore[union-attr]
        "Blackwell native (sm_120)"
    )
    assert health.overall_status == "FAIL"


def test_collect_runtime_health_marks_cpu_fallback_as_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_cuda = SimpleNamespace(is_available=lambda: False)
    fake_torch = SimpleNamespace(
        __version__="2.12.1",
        cuda=fake_cuda,
        version=SimpleNamespace(cuda=None),
    )

    monkeypatch.setattr(runtime_health, "package_version", lambda _name: "2.12.1")
    monkeypatch.setattr(runtime_health.importlib, "import_module", lambda _name: fake_torch)
    monkeypatch.setattr(runtime_health, "collect_runtime_diagnostics", _diagnostics)

    health = runtime_health.collect_runtime_health()

    assert health.by_name("CUDA").status == "WARN"  # type: ignore[union-attr]
    assert health.by_name("GPU").value == "CPU mode"  # type: ignore[union-attr]
    assert health.by_name("GPU architecture").value == "CPU mode"  # type: ignore[union-attr]
    assert health.overall_status == "WARN"


def test_blackwell_without_native_sm120_is_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_torch = SimpleNamespace(
        __version__="2.12.1+cu130",
        cuda=_blackwell_cuda(native=False),
        version=SimpleNamespace(cuda="13.0"),
    )
    monkeypatch.setattr(runtime_health, "package_version", lambda _name: "2.12.1")
    monkeypatch.setattr(runtime_health.importlib, "import_module", lambda _name: fake_torch)
    monkeypatch.setattr(runtime_health, "collect_runtime_diagnostics", _diagnostics)

    health = runtime_health.collect_runtime_health()

    architecture = health.by_name("GPU architecture")
    assert architecture is not None
    assert architecture.status == "FAIL"
    assert architecture.value == "Blackwell fallback (sm_120)"
    assert health.overall_status == "FAIL"


def test_cuda_128_is_rejected_for_v04_gpu_baseline(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_torch = SimpleNamespace(
        __version__="2.12.1+cu128",
        cuda=_blackwell_cuda(native=True, cuda_version="12.8"),
        version=SimpleNamespace(cuda="12.8"),
    )
    monkeypatch.setattr(runtime_health, "package_version", lambda _name: "2.12.1")
    monkeypatch.setattr(runtime_health.importlib, "import_module", lambda _name: fake_torch)
    monkeypatch.setattr(runtime_health, "collect_runtime_diagnostics", _diagnostics)

    health = runtime_health.collect_runtime_health()

    cuda = health.by_name("CUDA")
    assert cuda is not None
    assert cuda.status == "FAIL"
    assert cuda.value == "12.8"
    assert health.overall_status == "FAIL"
