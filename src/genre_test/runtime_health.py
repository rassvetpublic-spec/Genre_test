from __future__ import annotations

import importlib
import platform
import re
import shutil
import subprocess
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

MIN_TORCH_VERSION = (2, 12, 1)
TARGET_CUDA_PREFIX = "13.0"
BLACKWELL_MAJOR_CAPABILITIES = {10, 11, 12}
STATUS_ORDER = {"N/A": -1, "OK": 0, "WARN": 1, "FAIL": 2}
MIN_PYTHON_VERSION = (3, 12)
MAX_PYTHON_VERSION_EXCLUSIVE = (3, 14)


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
        return max(self.components, key=lambda item: STATUS_ORDER.get(item.status, 2)).status

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
            f"CUDA: {state('CUDA')} | GPU: {state('GPU architecture')} | "
            f"FFmpeg: {state('FFmpeg')} | HF: {state('HF auth')}"
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
    supported = MIN_PYTHON_VERSION <= sys.version_info[:2] < MAX_PYTHON_VERSION_EXCLUSIVE
    return RuntimeComponent(
        name="Python",
        status="OK" if supported else "FAIL",
        value=platform.python_version(),
        details="Supported: >=3.12,<3.14",
        category="Core",
    )


def _numeric_version(value: str) -> tuple[int, int, int]:
    base = value.split("+", 1)[0]
    numbers = [int(item) for item in re.findall(r"\d+", base)[:3]]
    while len(numbers) < 3:
        numbers.append(0)
    return tuple(numbers[:3])  # type: ignore[return-value]


def _nvidia_hardware_present() -> bool:
    if shutil.which("nvidia-smi"):
        return True
    if platform.system() != "Windows":
        return False

    shell = shutil.which("pwsh") or shutil.which("powershell") or shutil.which("powershell.exe")
    if not shell:
        return False
    command = (
        "$gpu = Get-CimInstance -ClassName Win32_VideoController -ErrorAction SilentlyContinue | "
        "Where-Object { $_.Name -match 'NVIDIA' -or $_.PNPDeviceID -match 'VEN_10DE' } | "
        "Select-Object -First 1; if ($gpu) { 'NVIDIA' }"
    )
    try:
        probe = subprocess.run(
            [shell, "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            timeout=4,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return "NVIDIA" in probe.stdout.upper()


def _torch_runtime_components(
    torch_package: RuntimeComponent,
    *,
    nvidia_hardware: bool | None = None,
) -> tuple[RuntimeComponent, ...]:
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
            RuntimeComponent(
                name="GPU architecture",
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
            RuntimeComponent(
                name="GPU architecture",
                status="FAIL",
                value="unavailable",
                details="PyTorch runtime could not be imported",
                category="Acceleration",
            ),
        )

    torch_version = str(getattr(torch, "__version__", torch_package.value))
    torch_version_ok = _numeric_version(torch_version) >= MIN_TORCH_VERSION
    cuda_available = bool(torch.cuda.is_available())

    if not cuda_available:
        if not torch_version_ok:
            return (
                RuntimeComponent(
                    name="CUDA",
                    status="FAIL",
                    value="unavailable",
                    details=f"PyTorch {torch_version} is below required 2.12.1",
                    category="Acceleration",
                ),
                RuntimeComponent(
                    name="GPU",
                    status="FAIL",
                    value="unavailable",
                    details="Acceleration runtime cannot use the required PyTorch baseline",
                    category="Acceleration",
                ),
                RuntimeComponent(
                    name="GPU architecture",
                    status="FAIL",
                    value="unavailable",
                    details="Architecture check unavailable with unsupported PyTorch",
                    category="Acceleration",
                ),
            )

        has_nvidia = _nvidia_hardware_present() if nvidia_hardware is None else nvidia_hardware
        if not has_nvidia:
            return (
                RuntimeComponent(
                    name="CUDA",
                    status="N/A",
                    value="not applicable",
                    details="CPU-only system; CUDA is not required",
                    category="Acceleration",
                ),
                RuntimeComponent(
                    name="GPU",
                    status="N/A",
                    value="CPU-only",
                    details="No NVIDIA hardware detected; CPU inference is expected",
                    category="Acceleration",
                ),
                RuntimeComponent(
                    name="GPU architecture",
                    status="N/A",
                    value="CPU-only",
                    details="Native CUDA architecture check is not applicable",
                    category="Acceleration",
                ),
            )

        return (
            RuntimeComponent(
                name="CUDA",
                status="FAIL",
                value="unavailable",
                details="NVIDIA hardware detected but PyTorch CUDA runtime is unavailable",
                category="Acceleration",
            ),
            RuntimeComponent(
                name="GPU",
                status="FAIL",
                value="NVIDIA unavailable to PyTorch",
                details="Run setup/driver repair or explicitly choose CPU mode",
                category="Acceleration",
            ),
            RuntimeComponent(
                name="GPU architecture",
                status="FAIL",
                value="not checked",
                details="CUDA must be available before the native architecture gate can run",
                category="Acceleration",
            ),
        )

    cuda_runtime = str(torch.version.cuda or "unknown")
    cuda_target_ok = cuda_runtime.startswith(TARGET_CUDA_PREFIX)
    cuda_status = "OK" if torch_version_ok and cuda_target_ok else "FAIL"
    cuda_component = RuntimeComponent(
        name="CUDA",
        status=cuda_status,
        value=cuda_runtime,
        details=(
            f"PyTorch {torch_version}; target >=2.12.1 / CUDA 13.0; "
            f"MAEST batch up to {DEFAULT_CUDA_BATCH_SIZE} windows"
        ),
        category="Acceleration",
    )

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

    try:
        major, minor = torch.cuda.get_device_capability(0)
        architecture = f"sm_{major}{minor}"
        compiled_arches = tuple(str(item) for item in torch.cuda.get_arch_list())
    except (AttributeError, OSError, RuntimeError, TypeError, ValueError) as exc:
        architecture_component = RuntimeComponent(
            name="GPU architecture",
            status="WARN",
            value="query unavailable",
            details=f"{type(exc).__name__}: {exc}",
            category="Acceleration",
        )
    else:
        native = architecture in compiled_arches
        blackwell = major in BLACKWELL_MAJOR_CAPABILITIES
        if blackwell and native and cuda_target_ok and torch_version_ok:
            arch_status = "OK"
            arch_value = f"Blackwell native ({architecture})"
        elif blackwell:
            arch_status = "FAIL"
            arch_value = f"Blackwell fallback ({architecture})"
        else:
            arch_status = "OK" if native else "WARN"
            arch_value = f"native ({architecture})" if native else f"fallback ({architecture})"
        architecture_component = RuntimeComponent(
            name="GPU architecture",
            status=arch_status,
            value=arch_value,
            details=(
                "Compiled CUDA arches: " + ", ".join(compiled_arches)
                if compiled_arches
                else "PyTorch did not report compiled CUDA architectures"
            ),
            category="Acceleration",
        )

    return cuda_component, gpu_component, architecture_component


def collect_runtime_health() -> RuntimeHealth:
    components: list[RuntimeComponent] = [_python_component()]
    package_items = [_package_component(distribution, label) for distribution, label in RUNTIME_PACKAGES]
    components.extend(package_items)

    torch_package = next(item for item in package_items if item.name == "PyTorch")
    components.extend(
        _torch_runtime_components(torch_package, nvidia_hardware=_nvidia_hardware_present())
    )

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
            status="OK",
            value="authenticated" if diagnostics.hf_token_available else "anonymous",
            details=(
                diagnostics.hf_auth_label
                + "; public pinned models support anonymous access; token is optional"
            ),
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
