from __future__ import annotations

import csv
import importlib
import shutil
import subprocess
import time
from dataclasses import dataclass
from io import StringIO

try:
    import psutil  # type: ignore
except ImportError:  # pragma: no cover - supported old-venv fallback
    psutil = None

MIB = 1024 * 1024
GIB = 1024 * MIB
NVIDIA_QUERY_FIELDS = (
    "index",
    "name",
    "utilization.gpu",
    "memory.used",
    "memory.total",
    "temperature.gpu",
    "power.draw",
    "power.limit",
)


@dataclass(frozen=True)
class GpuResourceSnapshot:
    index: int
    name: str
    utilization_percent: float | None
    memory_used_mib: float | None
    memory_total_mib: float | None
    temperature_c: float | None
    power_draw_w: float | None
    power_limit_w: float | None

    @property
    def memory_free_mib(self) -> float | None:
        if self.memory_used_mib is None or self.memory_total_mib is None:
            return None
        return max(0.0, self.memory_total_mib - self.memory_used_mib)

    @property
    def memory_percent(self) -> float | None:
        if not self.memory_total_mib or self.memory_used_mib is None:
            return None
        return 100.0 * self.memory_used_mib / self.memory_total_mib


@dataclass(frozen=True)
class TorchCudaMemorySnapshot:
    device_name: str
    allocated_mib: float
    reserved_mib: float
    peak_allocated_mib: float


@dataclass(frozen=True)
class ResourceSnapshot:
    sampled_at: float
    cpu_percent: float | None
    ram_used_bytes: int | None
    ram_available_bytes: int | None
    ram_total_bytes: int | None
    ram_percent: float | None
    process_rss_bytes: int | None
    process_cpu_percent: float | None
    gpu: GpuResourceSnapshot | None
    torch_cuda: TorchCudaMemorySnapshot | None
    system_status: str
    gpu_status: str


def _optional_float(value: str) -> float | None:
    text = value.strip()
    if not text or text.lower() in {"n/a", "na", "not supported", "[n/a]"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_nvidia_smi_csv(text: str) -> GpuResourceSnapshot | None:
    """Parse the first GPU row from our fixed `nvidia-smi --query-gpu` output."""
    rows = list(csv.reader(StringIO(text.strip())))
    if not rows:
        return None
    row = [item.strip() for item in rows[0]]
    if len(row) < len(NVIDIA_QUERY_FIELDS):
        return None
    try:
        index = int(row[0])
    except ValueError:
        return None
    return GpuResourceSnapshot(
        index=index,
        name=row[1],
        utilization_percent=_optional_float(row[2]),
        memory_used_mib=_optional_float(row[3]),
        memory_total_mib=_optional_float(row[4]),
        temperature_c=_optional_float(row[5]),
        power_draw_w=_optional_float(row[6]),
        power_limit_w=_optional_float(row[7]),
    )


def query_nvidia_gpu(timeout_seconds: float = 1.5) -> tuple[GpuResourceSnapshot | None, str]:
    executable = shutil.which("nvidia-smi")
    if not executable:
        return None, "nvidia-smi unavailable"
    command = [
        executable,
        "--query-gpu=" + ",".join(NVIDIA_QUERY_FIELDS),
        "--format=csv,noheader,nounits",
    ]
    try:
        probe = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "nvidia-smi timeout"
    except OSError as exc:
        return None, f"nvidia-smi error: {type(exc).__name__}"
    if probe.returncode != 0:
        return None, f"nvidia-smi exit {probe.returncode}"
    snapshot = parse_nvidia_smi_csv(probe.stdout)
    if snapshot is None:
        return None, "nvidia-smi output unavailable"
    return snapshot, "OK"


def query_torch_cuda_memory() -> TorchCudaMemorySnapshot | None:
    try:
        torch = importlib.import_module("torch")
    except (ImportError, OSError, RuntimeError):
        return None
    try:
        if not torch.cuda.is_available():
            return None
        return TorchCudaMemorySnapshot(
            device_name=str(torch.cuda.get_device_name(0)),
            allocated_mib=float(torch.cuda.memory_allocated(0) / MIB),
            reserved_mib=float(torch.cuda.memory_reserved(0) / MIB),
            peak_allocated_mib=float(torch.cuda.max_memory_allocated(0) / MIB),
        )
    except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
        return None


def _system_resources() -> tuple[
    float | None,
    int | None,
    int | None,
    int | None,
    float | None,
    int | None,
    float | None,
    str,
]:
    if psutil is None:
        return None, None, None, None, None, None, None, "psutil unavailable"
    try:
        cpu_percent = float(psutil.cpu_percent(interval=None))
        memory = psutil.virtual_memory()
        process = psutil.Process()
        rss = int(process.memory_info().rss)
        process_cpu = float(process.cpu_percent(interval=None))
    except (OSError, RuntimeError) as exc:
        return None, None, None, None, None, None, None, f"psutil error: {type(exc).__name__}"
    return (
        cpu_percent,
        int(memory.used),
        int(memory.available),
        int(memory.total),
        float(memory.percent),
        rss,
        process_cpu,
        "OK",
    )


def collect_resource_snapshot() -> ResourceSnapshot:
    (
        cpu_percent,
        ram_used,
        ram_available,
        ram_total,
        ram_percent,
        process_rss,
        process_cpu,
        system_status,
    ) = _system_resources()
    gpu, gpu_status = query_nvidia_gpu()
    torch_cuda = query_torch_cuda_memory()
    return ResourceSnapshot(
        sampled_at=time.time(),
        cpu_percent=cpu_percent,
        ram_used_bytes=ram_used,
        ram_available_bytes=ram_available,
        ram_total_bytes=ram_total,
        ram_percent=ram_percent,
        process_rss_bytes=process_rss,
        process_cpu_percent=process_cpu,
        gpu=gpu,
        torch_cuda=torch_cuda,
        system_status=system_status,
        gpu_status=gpu_status,
    )
