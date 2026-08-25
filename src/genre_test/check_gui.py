from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
import traceback
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .history import HistoryDB
from .logging_utils import append_log
from .runtime_meta import default_history_path, default_results_dir
from .validation import ValidationEngine, format_version_comparison

CHECK_DESCRIPTION = (
    "Проверка — сравнивает уже сохранённые результаты двух версий анализатора. "
    "Аудио повторно не анализируется."
)
CHECK_MODE_DESCRIPTION = (
    "Режим сравнения: Auto/Fast/Accurate/Expert — сравнить только результаты этого режима; "
    "«Любой последний» — взять последний доступный результат каждой версии."
)

VERSION_MODE_LABELS = {
    "Auto": "auto",
    "Fast": "fast",
    "Accurate": "accurate",
    "Expert": "expert",
    "Любой последний (диагностика)": "any",
}

SEPARATOR = "=" * 88


class CheckTab(ttk.Frame):
    """Compare persisted analyzer versions without re-running audio inference."""

    def __init__(self, master) -> None:
        super().__init__(master, padding=12)
        self.history_var = tk.StringVar(value=str(default_history_path()))
        self.out_var = tk.StringVar(value=str(default_results_dir() / "validation"))
        self.version_a_var = tk.StringVar()
        self.version_b_var = tk.StringVar()
        self.version_mode_var = tk.StringVar(value="Auto")
        self.status_var = tk.StringVar(value="Готов")
        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._busy = False
        self._build_ui()
        self.after(250, self._refresh_versions)
        self.after(120, self._poll_queue)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(5, weight=1)

        ttk.Label(
            self,
            text=CHECK_DESCRIPTION,
            wraplength=1000,
            justify="left",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 8))

        paths = ttk.Frame(self)
        paths.grid(row=1, column=0, sticky="ew", pady=4)
        paths.columnconfigure(1, weight=1)
        ttk.Label(paths, text="History SQLite:").grid(row=0, column=0, sticky="w")
        ttk.Entry(paths, textvariable=self.history_var).grid(
            row=0, column=1, sticky="ew", padx=(8, 8)
        )
        ttk.Button(paths, text="Выбрать", command=self._choose_history).grid(row=0, column=2)
        ttk.Button(paths, text="Открыть папку", command=self._open_history_folder).grid(
            row=0, column=3, padx=(8, 0)
        )
        ttk.Label(paths, text="Отчёты:").grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Entry(paths, textvariable=self.out_var).grid(
            row=1, column=1, sticky="ew", padx=(8, 8), pady=(4, 0)
        )
        ttk.Button(paths, text="Открыть", command=self._open_output).grid(
            row=1, column=2, pady=(4, 0)
        )

        controls = ttk.Frame(self)
        controls.grid(row=2, column=0, sticky="ew", pady=(8, 2))
        ttk.Label(controls, text="Версия A").pack(side="left")
        self.version_a_combo = ttk.Combobox(
            controls,
            textvariable=self.version_a_var,
            state="readonly",
            width=16,
        )
        self.version_a_combo.pack(side="left", padx=(6, 12))
        ttk.Label(controls, text="Версия B").pack(side="left")
        self.version_b_combo = ttk.Combobox(
            controls,
            textvariable=self.version_b_var,
            state="readonly",
            width=16,
        )
        self.version_b_combo.pack(side="left", padx=(6, 12))
        ttk.Label(controls, text="Режим").pack(side="left")
        ttk.Combobox(
            controls,
            textvariable=self.version_mode_var,
            values=tuple(VERSION_MODE_LABELS),
            state="readonly",
            width=31,
        ).pack(side="left", padx=(6, 12))
        ttk.Button(controls, text="Обновить", command=self._refresh_versions).pack(side="left")
        self.compare_button = ttk.Button(
            controls,
            text="СРАВНИТЬ",
            command=self._start_version_compare,
        )
        self.compare_button.pack(side="left", padx=(8, 0))
        ttk.Label(controls, textvariable=self.status_var).pack(side="left", padx=(12, 0))

        ttk.Label(
            self,
            text=CHECK_MODE_DESCRIPTION,
            wraplength=1000,
            justify="left",
        ).grid(row=3, column=0, sticky="ew", pady=(2, 8))

        ttk.Separator(self).grid(row=4, column=0, sticky="ew", pady=4)
        self.output = tk.Text(self, wrap="none", font=("Consolas", 10), undo=False)
        self.output.grid(row=5, column=0, sticky="nsew")
        yscroll = ttk.Scrollbar(self, orient="vertical", command=self.output.yview)
        yscroll.grid(row=5, column=1, sticky="ns")
        xscroll = ttk.Scrollbar(self, orient="horizontal", command=self.output.xview)
        xscroll.grid(row=6, column=0, sticky="ew")
        self.output.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        footer = ttk.Frame(self)
        footer.grid(row=7, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(
            footer,
            text="СКОПИРОВАТЬ СОДЕРЖИМОЕ",
            command=self._copy_output,
        ).pack(side="left")

    def _choose_history(self) -> None:
        selected = filedialog.askopenfilename(
            title="History SQLite",
            filetypes=[("SQLite", "*.sqlite3 *.sqlite *.db"), ("All", "*.*")],
            initialdir=str(Path(self.history_var.get()).expanduser().parent),
        )
        if selected:
            self.history_var.set(selected)
            self._refresh_versions()

    def _open_history_folder(self) -> None:
        path = Path(self.history_var.get()).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        os.startfile(path.parent)  # type: ignore[attr-defined]

    def _open_output(self) -> None:
        out = Path(self.out_var.get()).expanduser()
        out.mkdir(parents=True, exist_ok=True)
        os.startfile(out)  # type: ignore[attr-defined]

    def _copy_output(self) -> None:
        text = self.output.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        self.status_var.set("Содержимое скопировано в буфер")

    def _append_output(self, text: str, *, separator: bool = False) -> None:
        if not text:
            return
        if separator and self.output.index("end-1c") != "1.0":
            self.output.insert("end", f"\n{SEPARATOR}\n")
        self.output.insert("end", text.rstrip() + "\n")
        self.output.see("end")
        self.output.update_idletasks()

    def _refresh_versions(self) -> None:
        try:
            versions = HistoryDB(Path(self.history_var.get())).versions()
        except Exception:
            versions = []
        self.version_a_combo.configure(values=versions)
        self.version_b_combo.configure(values=versions)
        if versions:
            if self.version_a_var.get() not in versions:
                self.version_a_var.set(versions[-2] if len(versions) > 1 else versions[0])
            if self.version_b_var.get() not in versions:
                self.version_b_var.set(versions[-1])
        self.status_var.set(f"Версий в history: {len(versions)}")

    def _start_version_compare(self) -> None:
        if self._busy:
            return
        version_a = self.version_a_var.get()
        version_b = self.version_b_var.get()
        if not version_a or not version_b:
            messagebox.showerror(
                "Genre_test",
                "В истории недостаточно версий для сравнения.",
            )
            return
        self.output.delete("1.0", "end")
        self._append_output(
            f"Проверка версий: {version_a} -> {version_b} ({self.version_mode_var.get()})"
        )
        self._busy = True
        self.compare_button.configure(state="disabled")
        self.status_var.set("Сравнение…")
        threading.Thread(
            target=self._version_compare_worker,
            args=(version_a, version_b, VERSION_MODE_LABELS[self.version_mode_var.get()]),
            daemon=True,
        ).start()

    def _version_compare_worker(self, version_a: str, version_b: str, mode: str) -> None:
        try:
            engine = ValidationEngine(
                history_path=Path(self.history_var.get()),
                out_dir=Path(self.out_var.get()),
            )
            result = engine.compare_versions(version_a, version_b, mode=mode)
            self._queue.put(("done", format_version_comparison(result)))
        except Exception:
            detail = traceback.format_exc()
            append_log(f"Version comparison fatal error:\n{detail}")
            self._queue.put(("error", detail))

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "done":
                    self._append_output(str(payload), separator=True)
                    self._busy = False
                    self.compare_button.configure(state="normal")
                    self.status_var.set("Готово")
                elif kind == "error":
                    self._append_output(str(payload), separator=True)
                    self._busy = False
                    self.compare_button.configure(state="normal")
                    self.status_var.set("Ошибка")
                    messagebox.showerror(
                        "Genre_test",
                        "Проверка завершилась ошибкой. См. подробности в окне и журнале.",
                    )
        except queue.Empty:
            pass
        self.after(120, self._poll_queue)
