from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
import traceback
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .cancellation import AnalysisCancelled
from .history import HistoryDB
from .logging_utils import append_log
from .runtime_meta import default_history_path, default_log_path, default_results_dir
from .validation import ValidationEngine, format_validation_session, format_version_comparison

VALIDATION_MODE_LABELS = {
    "Авто": ("auto", False),
    "Быстрый": ("fast", False),
    "Точный": ("accurate", False),
    "Fast + Auto + Accurate": ("auto", True),
}

FILTER_LABELS = {
    "Все треки": "all",
    "Только результаты старых версий": "old_versions",
    "Только нестабильные": "unstable",
}

VERSION_MODE_LABELS = {
    "Любой последний": "any",
    "Auto": "auto",
    "Fast": "fast",
    "Accurate": "accurate",
    "Expert": "expert",
}


class ValidationTab(ttk.Frame):
    def __init__(self, master) -> None:
        super().__init__(master, padding=12)
        self.out_var = tk.StringVar(value=str(default_results_dir() / "validation"))
        self.history_var = tk.StringVar(value=str(default_history_path()))
        self.device_var = tk.StringVar(value="auto")
        self.mode_var = tk.StringVar(value="Fast + Auto + Accurate")
        self.filter_var = tk.StringVar(value="Только результаты старых версий")
        self.status_var = tk.StringVar(value="Готов")
        self.version_a_var = tk.StringVar()
        self.version_b_var = tk.StringVar()
        self.version_mode_var = tk.StringVar(value="Любой последний")
        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._cancel_event = threading.Event()
        self._busy = False
        self._build_ui()
        self.after(120, self._poll_queue)
        self.after(250, self._refresh_versions)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(7, weight=1)

        ttk.Label(self, text="Источники аудио (можно разные диски и каталоги):").grid(
            row=0, column=0, sticky="w"
        )
        source_frame = ttk.Frame(self)
        source_frame.grid(row=1, column=0, sticky="nsew", pady=(4, 8))
        source_frame.columnconfigure(0, weight=1)
        self.sources = tk.Listbox(source_frame, height=5, selectmode="extended")
        self.sources.grid(row=0, column=0, rowspan=4, sticky="nsew")
        ttk.Button(source_frame, text="+ Каталог", command=self._add_folder).grid(
            row=0, column=1, padx=(8, 0), pady=2, sticky="ew"
        )
        ttk.Button(source_frame, text="+ Файлы", command=self._add_files).grid(
            row=1, column=1, padx=(8, 0), pady=2, sticky="ew"
        )
        ttk.Button(source_frame, text="Удалить", command=self._remove_sources).grid(
            row=2, column=1, padx=(8, 0), pady=2, sticky="ew"
        )
        ttk.Button(
            source_frame,
            text="Очистить",
            command=lambda: self.sources.delete(0, "end"),
        ).grid(row=3, column=1, padx=(8, 0), pady=2, sticky="ew")

        paths = ttk.Frame(self)
        paths.grid(row=2, column=0, sticky="ew", pady=4)
        paths.columnconfigure(1, weight=1)
        ttk.Label(paths, text="History SQLite:").grid(row=0, column=0, sticky="w")
        ttk.Entry(paths, textvariable=self.history_var).grid(
            row=0, column=1, sticky="ew", padx=(8, 8)
        )
        ttk.Button(paths, text="Выбрать", command=self._choose_history).grid(row=0, column=2)
        ttk.Label(paths, text="Отчёты:").grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Entry(paths, textvariable=self.out_var).grid(
            row=1, column=1, sticky="ew", padx=(8, 8), pady=(4, 0)
        )
        ttk.Button(paths, text="Открыть", command=self._open_output).grid(
            row=1, column=2, pady=(4, 0)
        )
        ttk.Label(paths, text="Лог:").grid(row=2, column=0, sticky="w", pady=(4, 0))
        ttk.Label(paths, text=str(default_log_path())).grid(
            row=2, column=1, sticky="w", padx=(8, 8), pady=(4, 0)
        )
        ttk.Button(paths, text="Открыть лог", command=self._open_log).grid(
            row=2, column=2, pady=(4, 0)
        )

        settings = ttk.Frame(self)
        settings.grid(row=3, column=0, sticky="ew", pady=(6, 4))
        ttk.Label(settings, text="Device").pack(side="left")
        ttk.Combobox(
            settings,
            textvariable=self.device_var,
            values=("auto", "cuda", "cpu"),
            state="readonly",
            width=8,
        ).pack(side="left", padx=(6, 18))
        ttk.Label(settings, text="Перепроверка").pack(side="left")
        ttk.Combobox(
            settings,
            textvariable=self.filter_var,
            values=tuple(FILTER_LABELS),
            state="readonly",
            width=31,
        ).pack(side="left", padx=(6, 18))
        ttk.Label(settings, text="Режим").pack(side="left")
        ttk.Combobox(
            settings,
            textvariable=self.mode_var,
            values=tuple(VALIDATION_MODE_LABELS),
            state="readonly",
            width=23,
        ).pack(side="left", padx=(6, 0))

        actions = ttk.Frame(self)
        actions.grid(row=4, column=0, sticky="ew", pady=(4, 8))
        self.run_button = ttk.Button(
            actions,
            text="НАЧАТЬ ПЕРЕПРОВЕРКУ",
            command=self._start_validation,
        )
        self.run_button.pack(side="left")
        self.stop_button = ttk.Button(
            actions,
            text="ОСТАНОВИТЬ",
            command=self._request_stop,
            state="disabled",
        )
        self.stop_button.pack(side="left", padx=(8, 0))
        ttk.Button(
            actions,
            text="Импорт JSON файлов",
            command=self._import_json_files,
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            actions,
            text="Импорт папки JSON",
            command=self._import_json_folder,
        ).pack(side="left", padx=(8, 0))
        self.progress = ttk.Progressbar(actions, mode="indeterminate", length=160)
        self.progress.pack(side="left", padx=12)
        ttk.Label(actions, textvariable=self.status_var).pack(side="left")

        compare_frame = ttk.LabelFrame(
            self,
            text="Сравнение версий анализатора",
            padding=8,
        )
        compare_frame.grid(row=5, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(compare_frame, text="Версия A").pack(side="left")
        self.version_a_combo = ttk.Combobox(
            compare_frame,
            textvariable=self.version_a_var,
            state="readonly",
            width=16,
        )
        self.version_a_combo.pack(side="left", padx=(6, 12))
        ttk.Label(compare_frame, text="Версия B").pack(side="left")
        self.version_b_combo = ttk.Combobox(
            compare_frame,
            textvariable=self.version_b_var,
            state="readonly",
            width=16,
        )
        self.version_b_combo.pack(side="left", padx=(6, 12))
        ttk.Label(compare_frame, text="Режим").pack(side="left")
        ttk.Combobox(
            compare_frame,
            textvariable=self.version_mode_var,
            values=tuple(VERSION_MODE_LABELS),
            state="readonly",
            width=18,
        ).pack(side="left", padx=(6, 12))
        ttk.Button(compare_frame, text="Обновить", command=self._refresh_versions).pack(
            side="left"
        )
        ttk.Button(
            compare_frame,
            text="СРАВНИТЬ",
            command=self._start_version_compare,
        ).pack(side="left", padx=(8, 0))

        ttk.Separator(self).grid(row=6, column=0, sticky="ew", pady=4)
        self.output = tk.Text(self, wrap="none", font=("Consolas", 10), undo=False)
        self.output.grid(row=7, column=0, sticky="nsew")
        yscroll = ttk.Scrollbar(self, orient="vertical", command=self.output.yview)
        yscroll.grid(row=7, column=1, sticky="ns")
        self.output.configure(yscrollcommand=yscroll.set)

        footer = ttk.Frame(self)
        footer.grid(row=8, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(
            footer,
            text="СКОПИРОВАТЬ СОДЕРЖИМОЕ",
            command=self._copy_output,
        ).pack(side="left")

    def _source_values(self) -> list[Path]:
        return [Path(self.sources.get(index)) for index in range(self.sources.size())]

    def _append_source(self, path: str) -> None:
        current = {
            self.sources.get(index).casefold()
            for index in range(self.sources.size())
        }
        resolved = str(Path(path).resolve())
        if resolved.casefold() not in current:
            self.sources.insert("end", resolved)

    def _add_folder(self) -> None:
        selected = filedialog.askdirectory(title="Добавить каталог с аудио")
        if selected:
            self._append_source(selected)

    def _add_files(self) -> None:
        selected = filedialog.askopenfilenames(
            title="Добавить аудиофайлы",
            filetypes=[
                ("Audio", "*.wav *.flac *.mp3 *.ogg *.m4a *.aac"),
                ("All", "*.*"),
            ],
        )
        for path in selected:
            self._append_source(path)

    def _remove_sources(self) -> None:
        for index in reversed(self.sources.curselection()):
            self.sources.delete(index)

    def _choose_history(self) -> None:
        selected = filedialog.asksaveasfilename(
            title="History SQLite",
            defaultextension=".sqlite3",
            filetypes=[
                ("SQLite", "*.sqlite3 *.sqlite *.db"),
                ("All", "*.*"),
            ],
            initialdir=str(default_history_path().parent),
            initialfile=Path(self.history_var.get()).name,
        )
        if selected:
            self.history_var.set(selected)
            self._refresh_versions()

    def _open_output(self) -> None:
        out = Path(self.out_var.get()).expanduser()
        out.mkdir(parents=True, exist_ok=True)
        os.startfile(out)  # type: ignore[attr-defined]

    def _open_log(self) -> None:
        path = default_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
        os.startfile(path)  # type: ignore[attr-defined]

    def _copy_output(self) -> None:
        text = self.output.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        self.status_var.set("Содержимое скопировано в буфер")

    def _set_busy(self, busy: bool, status: str, stoppable: bool = False) -> None:
        self._busy = busy
        self.run_button.configure(state="disabled" if busy else "normal")
        self.stop_button.configure(state="normal" if busy and stoppable else "disabled")
        if busy:
            self.progress.start(10)
        else:
            self.progress.stop()
        self.status_var.set(status)

    def _request_stop(self) -> None:
        if not self._busy or self._cancel_event.is_set():
            return
        self._cancel_event.set()
        self.stop_button.configure(state="disabled")
        self.status_var.set("Остановка после текущего безопасного шага…")
        append_log("Validation safe stop requested by user")

    def _start_validation(self) -> None:
        if self._busy:
            return
        sources = self._source_values()
        if not sources:
            messagebox.showerror(
                "Genre_test",
                "Добавьте хотя бы один каталог или аудиофайл.",
            )
            return
        mode, compare_all = VALIDATION_MODE_LABELS[self.mode_var.get()]
        filter_mode = FILTER_LABELS[self.filter_var.get()]
        self.output.delete("1.0", "end")
        self._cancel_event.clear()
        self._set_busy(True, "Подготовка validation…", stoppable=True)
        append_log(
            f"Validation started: sources={len(sources)}; mode={mode}; "
            f"compare_all={compare_all}; filter={filter_mode}"
        )
        threading.Thread(
            target=self._validation_worker,
            args=(sources, mode, compare_all, filter_mode),
            daemon=True,
        ).start()

    def _validation_worker(
        self,
        sources: list[Path],
        mode: str,
        compare_all: bool,
        filter_mode: str,
    ) -> None:
        try:
            engine = ValidationEngine(
                history_path=Path(self.history_var.get()),
                out_dir=Path(self.out_var.get()),
                device=self.device_var.get(),
            )

            def progress(current: int, total: int, message: str) -> None:
                self._queue.put(("status", f"[{current}/{total}] {message}"))

            result = engine.recheck(
                sources,
                mode=mode,
                compare_all_modes=compare_all,
                filter_mode=filter_mode,
                progress=progress,
                cancel_check=self._cancel_event.is_set,
            )
            kind = "cancelled" if result.cancelled else "done"
            self._queue.put((kind, format_validation_session(result)))
            self._queue.put(("refresh_versions", None))
        except AnalysisCancelled:
            message = "Остановлено пользователем до начала analysis session. История не повреждена."
            append_log(message)
            self._queue.put(("cancelled", message))
        except Exception:
            detail = traceback.format_exc()
            append_log(f"Validation fatal error:\n{detail}")
            self._queue.put(("error", detail))

    def _import_json_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Импортировать genre JSON",
            filetypes=[("Genre JSON", "*.json"), ("All", "*.*")],
        )
        if paths:
            self._start_import([Path(path) for path in paths])

    def _import_json_folder(self) -> None:
        selected = filedialog.askdirectory(title="Каталог с genre JSON")
        if selected:
            self._start_import([Path(selected)])

    def _start_import(self, sources: list[Path]) -> None:
        if self._busy:
            return
        self._cancel_event.clear()
        self._set_busy(True, "Импорт истории…", stoppable=False)
        threading.Thread(
            target=self._import_worker,
            args=(sources,),
            daemon=True,
        ).start()

    def _import_worker(self, sources: list[Path]) -> None:
        try:
            engine = ValidationEngine(history_path=Path(self.history_var.get()))
            imported, skipped = engine.import_history_sources(sources)
            self._queue.put(
                (
                    "done",
                    f"Импортировано: {imported}\nПропущено/не сопоставлено: {skipped}",
                )
            )
            self._queue.put(("refresh_versions", None))
        except Exception:
            detail = traceback.format_exc()
            append_log(f"History import fatal error:\n{detail}")
            self._queue.put(("error", detail))

    def _refresh_versions(self) -> None:
        try:
            versions = HistoryDB(Path(self.history_var.get())).versions()
        except Exception:
            versions = []
        self.version_a_combo.configure(values=versions)
        self.version_b_combo.configure(values=versions)
        if versions:
            if self.version_a_var.get() not in versions:
                self.version_a_var.set(
                    versions[-2] if len(versions) > 1 else versions[0]
                )
            if self.version_b_var.get() not in versions:
                self.version_b_var.set(versions[-1])

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
        self._cancel_event.clear()
        self._set_busy(True, "Сравнение версий…", stoppable=False)
        threading.Thread(
            target=self._version_compare_worker,
            args=(
                version_a,
                version_b,
                VERSION_MODE_LABELS[self.version_mode_var.get()],
            ),
            daemon=True,
        ).start()

    def _version_compare_worker(
        self,
        version_a: str,
        version_b: str,
        mode: str,
    ) -> None:
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
                if kind == "status":
                    self.status_var.set(str(payload))
                elif kind == "done":
                    self.output.insert("end", str(payload).lstrip() + "\n")
                    self.output.see("1.0")
                    self._set_busy(False, "Готово")
                elif kind == "cancelled":
                    self.output.insert("end", str(payload).lstrip() + "\n")
                    self.output.see("1.0")
                    self._set_busy(False, "Остановлено")
                elif kind == "refresh_versions":
                    self._refresh_versions()
                elif kind == "error":
                    self.output.insert("end", str(payload))
                    self._set_busy(False, "Ошибка")
                    messagebox.showerror(
                        "Genre_test",
                        "Операция завершилась ошибкой. См. подробности в окне и журнале.",
                    )
        except queue.Empty:
            pass
        self.after(120, self._poll_queue)
