from __future__ import annotations

import importlib
import platform
import sys
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

from .model_config import (
    DEFAULT_CUDA_BATCH_SIZE,
    DEFAULT_MODEL_REVISION,
    DEFAULT_SEMANTIC_MODEL_REVISION,
)
from .runtime_diagnostics import collect_runtime_diagnostics

RUNTIME_PACKAGES: tuple[tuple[str, str], ...] = (
    ("numpy", "NumPy"),
    ("scipy", "SciPy"),
    ("soundfile", "SoundFile"),
    ("librosa", "librosa"),
    ("torch", "PyTorch"),
    ("transformers", "Transformers"),
    ("accelerate", "Accelerate"),
    ("safetensors", "Safetensors"),
    ("typer", "Typer"),
    ("rich", "Rich"),
    ("pydantic", "Pydantic"),
    ("huggingface-hub", "Hugging Face Hub"),
)

STATUS_ORDER = {"OK": 0, "WARN": 1, "FAIL": 2}


@dataclass(frozen=True)
class RuntimeComponent:
    name: str
    status: str
    value: str
    details: str = ""
    category: str = "Runtime"


@dataclass(frozen=True)
class RuntimeHealth:
    components: tuple[RuntimeComponent, ...]

    @property
    def overall_status(self) -> str:
        if not self.components:
            return "FAIL"
        return max(self.components, key=lambda item: STATUS_ORDER[item.status]).status

    @property
    def package_components(self) -> tuple[RuntimeComponent, ...]:
        return tuple(item for item in self.components if item.category == "Package")

    @property
    def package_ok_count(self) -> int:
        return sum(item.status == "OK" for item in self.package_components)

    @property
    def package_count(self) -> int:
        return len(self.package_components)

    def by_name(self, name: str) -> RuntimeComponent | None:
        return next((item for item in self.components if item.name == name), None)

    @property
    def compact_summary(self) -> str:
        def state(name: str) -> str:
            item = self.by_name(name)
            return item.status if item else "FAIL"

        return (
            f"Deps: {self.package_ok_count}/{self.package_count} | "
            f"CUDA: {state('CUDA')} | FFmpeg: {state('FFmpeg')} | "
            f"HF: {state('HF auth')}"
        )


def _package_component(distribution: str, label: str) -> RuntimeComponent:
    try:
        installed = package_version(distribution)
    except PackageNotFoundError:
        return RuntimeComponent(
            name=label,
            status="FAIL",
            value="MISSING",
            details=f"Python distribution '{distribution}' is not installed",
            category="Package",
        )
    return RuntimeComponent(
        name=label,
        status="OK",
        value=installed,
        details=distribution,
        category="Package",
    )


def _python_component() -> RuntimeComponent:
    supported = (3, 11) <= sys.version_info[:2] < (3, 13)
    return RuntimeComponent(
        name="Python",
        status="OK" if supported else "FAIL",
        value=platform.python_version(),
        details="Supported: >=3.11,<3.13",
        category="Core",
    )


def _torch_runtime_components(torch_package: RuntimeComponent) -> tuple[RuntimeComponent, ...]:
    if torch_package.status != "OK":
        return (
            RuntimeComponent(
                name="CUDA",
                status="FAIL",
                value="unavailable",
                details="PyTorch is missing",
                category="Acceleration",
            ),
            RuntimeComponent(
                name="GPU",
                status="FAIL",
                value="unavailable",
                details="PyTorch is missing",
                category="Acceleration",
            ),
        )

    try:
        torch = importlib.import_module("torch")
    except (ImportError, OSError, RuntimeError) as exc:
        return (
            RuntimeComponent(
                name="CUDA",
                status="FAIL",
                value="torch import failed",
                details=f"{type(exc).__name__}: {exc}",
                category="Acceleration",
            ),
            RuntimeComponent(
                name="GPU",
                status="FAIL",
                value="unavailable",
                details="PyTorch runtime could not be imported",
                category="Acceleration",
            ),
        )

    cuda_available = bool(torch.cuda.is_available())
    cuda_runtime = str(torch.version.cuda or "unknown") if cuda_available else "unavailable"
    cuda_component = RuntimeComponent(
        name="CUDA",
        status="OK" if cuda_available else "WARN",
        value=cuda_runtime,
        details=(
            f"Default MAEST inference batch: up to {DEFAULT_CUDA_BATCH_SIZE} windows"
            if cuda_available
            else "CPU fallback is available"
        ),
        category="Acceleration",
    )
    if cuda_available:
        try:
            gpu_name = str(torch.cuda.get_device_name(0))
        except (OSError, RuntimeError) as exc:
            gpu_name = f"query failed: {type(exc).__name__}"
            gpu_status = "WARN"
        else:
            gpu_status = "OK"
        gpu_component = RuntimeComponent(
            name="GPU",
            status=gpu_status,
            value=gpu_name,
            details="CUDA device 0; shared by MAEST and AudioSet AST",
            category="Acceleration",
        )
    else:
        gpu_component = RuntimeComponent(
            name="GPU",
            status="WARN",
            value="CPU mode",
            details="No CUDA GPU available to PyTorch",
            category="Acceleration",
        )
    return cuda_component, gpu_component


def collect_runtime_health() -> RuntimeHealth:
    components: list[RuntimeComponent] = [_python_component()]
    package_items = [_package_component(distribution, label) for distribution, label in RUNTIME_PACKAGES]
    components.extend(package_items)

    torch_package = next(item for item in package_items if item.name == "PyTorch")
    components.extend(_torch_runtime_components(torch_package))

    diagnostics = collect_runtime_diagnostics()
    components.append(
        RuntimeComponent(
            name="FFmpeg",
            status="OK" if diagnostics.ffmpeg_available else "WARN",
            value=diagnostics.ffmpeg_path or "MISSING",
            details=(
                "AAC/M4A and extended decode fallback available"
                if diagnostics.ffmpeg_available
                else "AAC/M4A and extended decode fallback unavailable"
            ),
            category="External",
        )
    )
    components.append(
        RuntimeComponent(
            name="HF auth",
            status="OK" if diagnostics.hf_token_available else "WARN",
            value="authenticated" if diagnostics.hf_token_available else "anonymous",
            details=diagnostics.hf_auth_label,
            category="External",
        )
    )
    components.append(
        RuntimeComponent(
            name="MAEST revision",
            status="OK" if DEFAULT_MODEL_REVISION else "FAIL",
            value=DEFAULT_MODEL_REVISION or "UNPINNED",
            details="Pinned Discogs519 fine-style model",
            category="Model",
        )
    )
    components.append(
        RuntimeComponent(
            name="AudioSet AST revision",
            status="OK" if DEFAULT_SEMANTIC_MODEL_REVISION else "FAIL",
            value=DEFAULT_SEMANTIC_MODEL_REVISION or "UNPINNED",
            details="Pinned independent semantic/audio-event model; downloaded lazily",
            category="Model",
        )
    )
    return RuntimeHealth(tuple(components))
