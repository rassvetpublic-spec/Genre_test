from __future__ import annotations

import threading
import tkinter as tk
import traceback
from pathlib import Path
from tkinter import messagebox, ttk

from .build_compare import compare_builds, compare_repeatability, format_build_comparison
from .build_history import BuildAwareHistoryDB, BuildInfo
from .check_gui import CheckTab, VERSION_MODE_LABELS
from .logging_utils import append_log

BETWEEN_BUILDS = "Сборки A → B"
REPEATABILITY = "Повторяемость A"
CHECK_DESCRIPTION = (
    "Проверка — сравнивает сохранённые сборки анализатора без повторного анализа аудио. "
    "Сборка учитывает версию, Git commit, schema и ревизию модели."
)
CHECK_MODE_DESCRIPTION = (
    "Сборки A → B — сравнение результатов двух конкретных сборок. "
    "Повторяемость A — сравнение двух последних запусков одной сборки A. "
    "Режим Auto/Fast/Accurate/Expert ограничивает сравнение этим режимом."
)


class BuildAwareCheckTab(CheckTab):
    def __init__(self, master) -> None:
        self._builds_by_label: dict[str, BuildInfo] = {}
        super().__init__(master)
        self.kind_var = tk.StringVar(self, value=BETWEEN_BUILDS)
        self._decorate_build_ui()
        self.after_idle(self._refresh_versions)

    def _decorate_build_ui(self) -> None:
        for child in self.winfo_children():
            if isinstance(child, ttk.Label):
                text = str(child.cget("text"))
                if text.startswith("Проверка —"):
                    child.configure(text=CHECK_DESCRIPTION)
                elif text.startswith("Режим сравнения:"):
                    child.configure(text=CHECK_MODE_DESCRIPTION)
            if not isinstance(child, ttk.Frame):
                continue
            labels = [
                nested
                for nested in child.winfo_children()
                if isinstance(nested, ttk.Label)
            ]
            texts = {str(label.cget("text")) for label in labels}
            if "Версия A" not in texts or "Версия B" not in texts:
                continue
            for label in labels:
                if str(label.cget("text")) == "Версия A":
                    label.configure(text="Сборка A")
                elif str(label.cget("text")) == "Версия B":
                    label.configure(text="Сборка B")
            self.version_a_combo.configure(width=43)
            self.version_b_combo.configure(width=43)
            ttk.Label(child, text="Тип").pack(side="left", padx=(8, 0))
            ttk.Combobox(
                child,
                textvariable=self.kind_var,
                values=(BETWEEN_BUILDS, REPEATABILITY),
                state="readonly",
                width=18,
            ).pack(side="left", padx=(6, 0))
            break

    def _refresh_versions(self) -> None:
        try:
            builds = BuildAwareHistoryDB(Path(self.history_var.get())).builds()
        except Exception:  # noqa: BLE001 - keep GUI usable for invalid/external history DBs
            builds = []
        self._builds_by_label = {build.label: build for build in builds}
        labels = list(self._builds_by_label)
        self.version_a_combo.configure(values=labels)
        self.version_b_combo.configure(values=labels)
        if labels:
            if self.version_a_var.get() not in self._builds_by_label:
                self.version_a_var.set(labels[-2] if len(labels) > 1 else labels[0])
            if self.version_b_var.get() not in self._builds_by_label:
                self.version_b_var.set(labels[-1])
        else:
            self.version_a_var.set("")
            self.version_b_var.set("")
        self.status_var.set(f"Сборок в history: {len(labels)}")

    def _start_version_compare(self) -> None:
        if self._busy:
            return
        label_a = self.version_a_var.get()
        label_b = self.version_b_var.get()
        build_a = self._builds_by_label.get(label_a)
        build_b = self._builds_by_label.get(label_b)
        kind = self.kind_var.get()
        if build_a is None:
            messagebox.showerror("Genre_test", "Выберите сохранённую сборку A.")
            return
        if kind == BETWEEN_BUILDS:
            if build_b is None:
                messagebox.showerror("Genre_test", "Выберите сохранённую сборку B.")
                return
            if build_a.key == build_b.key:
                messagebox.showerror(
                    "Genre_test",
                    "Для одной сборки используйте тип «Повторяемость A».",
                )
                return

        mode_label = self.version_mode_var.get()
        mode = VERSION_MODE_LABELS[mode_label]
        self.output.delete("1.0", "end")
        if kind == REPEATABILITY:
            self._append_output(f"Повторяемость сборки: {build_a.label} ({mode_label})")
        else:
            assert build_b is not None
            self._append_output(
                f"Проверка сборок: {build_a.label} -> {build_b.label} ({mode_label})"
            )
        self._busy = True
        self.compare_button.configure(state="disabled")
        self.status_var.set("Сравнение…")
        threading.Thread(
            target=self._build_compare_worker,
            args=(build_a, build_b, mode, kind),
            daemon=True,
        ).start()

    def _build_compare_worker(
        self,
        build_a: BuildInfo,
        build_b: BuildInfo | None,
        mode: str,
        kind: str,
    ) -> None:
        try:
            history = BuildAwareHistoryDB(Path(self.history_var.get()))
            out_dir = Path(self.out_var.get())
            if kind == REPEATABILITY:
                result = compare_repeatability(history, build_a, mode=mode, out_dir=out_dir)
            else:
                assert build_b is not None
                result = compare_builds(history, build_a, build_b, mode=mode, out_dir=out_dir)
            self._queue.put(("done", format_build_comparison(*result)))
        except Exception:  # noqa: BLE001 - report unexpected comparison failures in GUI/log
            detail = traceback.format_exc()
            append_log(f"Build comparison fatal error:\n{detail}")
            self._queue.put(("error", detail))
