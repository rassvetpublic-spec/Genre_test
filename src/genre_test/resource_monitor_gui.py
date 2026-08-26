from __future__ import annotations

import datetime as dt
import queue
import threading
import tkinter as tk
from tkinter import ttk

from . import __version__
from .resource_monitor import GIB, MIB, ResourceSnapshot, collect_resource_snapshot

REFRESH_MS = 1000
POLL_MS = 100


def _format_bytes(value: int | None) -> str:
    if value is None:
        return "N/A"
    if value >= GIB:
        return f"{value / GIB:.2f} GiB"
    return f"{value / MIB:.1f} MiB"


def _format_percent(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.1f}%"


def _format_mib(value: float | None) -> str:
    if value is None:
        return "N/A"
    if value >= 1024:
        return f"{value / 1024:.2f} GiB"
    return f"{value:.0f} MiB"


def _clamp_percent(value: float | None) -> float:
    if value is None:
        return 0.0
    return max(0.0, min(100.0, value))


class ResourceMonitorWindow(tk.Toplevel):
    """Live CPU/RAM/GPU/VRAM monitor that stays independent from analysis results."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.title(f"Genre_test v{__version__} — Resource Monitor")
        self.geometry("720x610")
        self.minsize(620, 520)
        self.transient(parent)

        self._active = True
        self._paused = False
        self._in_flight = False
        self._after_id: str | None = None
        self._queue: queue.Queue[ResourceSnapshot | BaseException] = queue.Queue()
        self._bars: dict[str, ttk.Progressbar] = {}
        self._vars: dict[str, tk.StringVar] = {}

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._schedule(50)

    def _var(self, name: str, value: str = "N/A") -> tk.StringVar:
        variable = tk.StringVar(self, value=value)
        self._vars[name] = variable
        return variable

    def _build_gauge(self, parent: ttk.Frame, row: int, key: str, label: str) -> None:
        ttk.Label(parent, text=label, width=22).grid(row=row, column=0, sticky="w", pady=5)
        bar = ttk.Progressbar(parent, mode="determinate", maximum=100)
        bar.grid(row=row, column=1, sticky="ew", padx=(8, 10), pady=5)
        self._bars[key] = bar
        ttk.Label(parent, textvariable=self._var(key), width=26).grid(
            row=row,
            column=2,
            sticky="e",
            pady=5,
        )

    def _build_value(self, parent: ttk.Frame, row: int, key: str, label: str) -> None:
        ttk.Label(parent, text=label, width=22).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Label(parent, textvariable=self._var(key)).grid(
            row=row,
            column=1,
            columnspan=2,
            sticky="w",
            padx=(8, 0),
            pady=4,
        )

    def _build_ui(self) -> None:
        header = ttk.Frame(self, padding=(12, 10))
        header.pack(fill="x")
        ttk.Label(
            header,
            text="Живой монитор ресурсов",
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left")
        ttk.Button(header, text="Обновить сейчас", command=self._request_refresh).pack(
            side="right",
            padx=(8, 0),
        )
        self.pause_button = ttk.Button(header, text="Пауза", command=self._toggle_pause)
        self.pause_button.pack(side="right")

        status = ttk.Frame(self, padding=(12, 0, 12, 8))
        status.pack(fill="x")
        ttk.Label(status, textvariable=self._var("status", "Запуск мониторинга…")).pack(
            side="left"
        )
        ttk.Label(status, textvariable=self._var("sample_time", "")).pack(side="right")

        system = ttk.LabelFrame(self, text="Система", padding=10)
        system.pack(fill="x", padx=12, pady=(0, 8))
        system.columnconfigure(1, weight=1)
        self._build_gauge(system, 0, "cpu", "CPU")
        self._build_gauge(system, 1, "ram", "RAM")
        self._build_value(system, 2, "ram_detail", "RAM подробно")

        process = ttk.LabelFrame(self, text="Процесс Genre_test", padding=10)
        process.pack(fill="x", padx=12, pady=(0, 8))
        process.columnconfigure(1, weight=1)
        self._build_gauge(process, 0, "process_cpu", "CPU процесса")
        self._build_value(process, 1, "process_rss", "RAM процесса")

        gpu = ttk.LabelFrame(self, text="NVIDIA GPU", padding=10)
        gpu.pack(fill="x", padx=12, pady=(0, 8))
        gpu.columnconfigure(1, weight=1)
        self._build_value(gpu, 0, "gpu_name", "Устройство")
        self._build_gauge(gpu, 1, "gpu_usage", "GPU load")
        self._build_gauge(gpu, 2, "vram", "VRAM")
        self._build_value(gpu, 3, "gpu_temperature", "Температура")
        self._build_value(gpu, 4, "gpu_power", "Питание")

        cuda = ttk.LabelFrame(self, text="PyTorch CUDA — текущий процесс", padding=10)
        cuda.pack(fill="x", padx=12, pady=(0, 8))
        cuda.columnconfigure(1, weight=1)
        self._build_value(cuda, 0, "torch_device", "CUDA device")
        self._build_value(cuda, 1, "torch_allocated", "Allocated")
        self._build_value(cuda, 2, "torch_reserved", "Reserved")
        self._build_value(cuda, 3, "torch_peak", "Peak allocated")

        footer = ttk.Frame(self, padding=(12, 0, 12, 10))
        footer.pack(fill="x")
        ttk.Label(
            footer,
            text=(
                "GPU/VRAM system-wide берутся из nvidia-smi; allocated/reserved — "
                "только память CUDA процесса Genre_test."
            ),
            wraplength=560,
            justify="left",
        ).pack(side="left", fill="x", expand=True)
        ttk.Button(footer, text="Закрыть", command=self._close).pack(side="right", padx=(10, 0))

    def _schedule(self, delay_ms: int) -> None:
        if not self._active:
            return
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except tk.TclError:
                pass
        self._after_id = self.after(delay_ms, self._tick)

    def _tick(self) -> None:
        self._after_id = None
        if not self._active:
            return

        updated = False
        while True:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                break
            self._in_flight = False
            updated = True
            if isinstance(item, BaseException):
                self._vars["status"].set(f"Ошибка мониторинга: {type(item).__name__}: {item}")
            else:
                self._apply_snapshot(item)

        if not self._paused and not self._in_flight and (updated or self._queue.empty()):
            self._start_worker()
        self._schedule(REFRESH_MS if updated else POLL_MS)

    def _start_worker(self) -> None:
        if self._in_flight or self._paused or not self._active:
            return
        self._in_flight = True

        def worker() -> None:
            try:
                self._queue.put(collect_resource_snapshot())
            except BaseException as exc:  # monitor must never kill the main GUI
                self._queue.put(exc)

        threading.Thread(target=worker, name="genre-test-resource-monitor", daemon=True).start()

    def _request_refresh(self) -> None:
        if self._paused:
            self._paused = False
            self.pause_button.configure(text="Пауза")
        if not self._in_flight:
            self._start_worker()
        self._schedule(POLL_MS)

    def _toggle_pause(self) -> None:
        self._paused = not self._paused
        self.pause_button.configure(text="Продолжить" if self._paused else "Пауза")
        self._vars["status"].set("Мониторинг приостановлен" if self._paused else "Мониторинг…")
        if not self._paused:
            self._request_refresh()

    def _apply_snapshot(self, snapshot: ResourceSnapshot) -> None:
        stamp = dt.datetime.fromtimestamp(snapshot.sampled_at).strftime("%H:%M:%S")
        self._vars["sample_time"].set(f"Обновлено: {stamp}")
        self._vars["status"].set(
            f"System: {snapshot.system_status} | GPU: {snapshot.gpu_status} | ~1 s"
        )

        self._bars["cpu"]["value"] = _clamp_percent(snapshot.cpu_percent)
        self._vars["cpu"].set(_format_percent(snapshot.cpu_percent))

        self._bars["ram"]["value"] = _clamp_percent(snapshot.ram_percent)
        self._vars["ram"].set(_format_percent(snapshot.ram_percent))
        self._vars["ram_detail"].set(
            f"{_format_bytes(snapshot.ram_used_bytes)} used / "
            f"{_format_bytes(snapshot.ram_total_bytes)} total / "
            f"{_format_bytes(snapshot.ram_available_bytes)} available"
        )

        self._bars["process_cpu"]["value"] = _clamp_percent(snapshot.process_cpu_percent)
        self._vars["process_cpu"].set(_format_percent(snapshot.process_cpu_percent))
        self._vars["process_rss"].set(_format_bytes(snapshot.process_rss_bytes))

        gpu = snapshot.gpu
        if gpu is None:
            self._vars["gpu_name"].set("N/A")
            self._bars["gpu_usage"]["value"] = 0
            self._vars["gpu_usage"].set("N/A")
            self._bars["vram"]["value"] = 0
            self._vars["vram"].set("N/A")
            self._vars["gpu_temperature"].set("N/A")
            self._vars["gpu_power"].set("N/A")
        else:
            self._vars["gpu_name"].set(f"GPU {gpu.index}: {gpu.name}")
            self._bars["gpu_usage"]["value"] = _clamp_percent(gpu.utilization_percent)
            self._vars["gpu_usage"].set(_format_percent(gpu.utilization_percent))
            self._bars["vram"]["value"] = _clamp_percent(gpu.memory_percent)
            self._vars["vram"].set(
                f"{_format_mib(gpu.memory_used_mib)} used / "
                f"{_format_mib(gpu.memory_total_mib)} total / "
                f"{_format_mib(gpu.memory_free_mib)} free"
            )
            self._vars["gpu_temperature"].set(
                "N/A" if gpu.temperature_c is None else f"{gpu.temperature_c:.0f} °C"
            )
            if gpu.power_draw_w is None:
                self._vars["gpu_power"].set("N/A")
            elif gpu.power_limit_w is None:
                self._vars["gpu_power"].set(f"{gpu.power_draw_w:.1f} W")
            else:
                self._vars["gpu_power"].set(
                    f"{gpu.power_draw_w:.1f} W / {gpu.power_limit_w:.1f} W limit"
                )

        cuda = snapshot.torch_cuda
        if cuda is None:
            self._vars["torch_device"].set("CUDA unavailable / no active CUDA context")
            self._vars["torch_allocated"].set("N/A")
            self._vars["torch_reserved"].set("N/A")
            self._vars["torch_peak"].set("N/A")
        else:
            self._vars["torch_device"].set(cuda.device_name)
            self._vars["torch_allocated"].set(_format_mib(cuda.allocated_mib))
            self._vars["torch_reserved"].set(_format_mib(cuda.reserved_mib))
            self._vars["torch_peak"].set(_format_mib(cuda.peak_allocated_mib))

    def _close(self) -> None:
        self._active = False
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None
        self.destroy()
