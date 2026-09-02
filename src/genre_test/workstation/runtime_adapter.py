from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any


def _round(value: float | None, digits: int = 1) -> float | None:
    return None if value is None else round(float(value), digits)


def _mib_from_bytes(value: int | None) -> float | None:
    if value is None:
        return None
    return round(float(value) / (1024 * 1024), 1)


def collect_runtime_hud(
    collector: Callable[[], Any] | None = None,
) -> dict[str, object]:
    if collector is None:
        module = importlib.import_module("genre_test.resource_monitor")
        collector = module.collect_resource_snapshot
    snapshot = collector()
    gpu = snapshot.gpu
    torch_cuda = snapshot.torch_cuda
    return {
        "sampled_at": snapshot.sampled_at,
        "system_status": snapshot.system_status,
        "gpu_status": snapshot.gpu_status,
        "cpu_percent": _round(snapshot.cpu_percent),
        "ram": {
            "used_mib": _mib_from_bytes(snapshot.ram_used_bytes),
            "available_mib": _mib_from_bytes(snapshot.ram_available_bytes),
            "total_mib": _mib_from_bytes(snapshot.ram_total_bytes),
            "percent": _round(snapshot.ram_percent),
        },
        "process": {
            "rss_mib": _mib_from_bytes(snapshot.process_rss_bytes),
            "cpu_percent": _round(snapshot.process_cpu_percent),
        },
        "gpu": None
        if gpu is None
        else {
            "index": gpu.index,
            "name": gpu.name,
            "utilization_percent": _round(gpu.utilization_percent),
            "memory_used_mib": _round(gpu.memory_used_mib),
            "memory_free_mib": _round(gpu.memory_free_mib),
            "memory_total_mib": _round(gpu.memory_total_mib),
            "memory_percent": _round(gpu.memory_percent),
            "temperature_c": _round(gpu.temperature_c),
            "power_draw_w": _round(gpu.power_draw_w),
            "power_limit_w": _round(gpu.power_limit_w),
        },
        "torch_cuda": None
        if torch_cuda is None
        else {
            "device_name": torch_cuda.device_name,
            "allocated_mib": _round(torch_cuda.allocated_mib),
            "reserved_mib": _round(torch_cuda.reserved_mib),
            "peak_allocated_mib": _round(torch_cuda.peak_allocated_mib),
        },
        "active_backend": None,
        "active_model": None,
        "active_job": None,
    }
