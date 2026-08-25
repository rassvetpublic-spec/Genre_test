from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
import traceback
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .audio import iter_audio_files
from .cancellation import AnalysisCancelled
from .gui_text import bind_copy_shortcuts
from .history import HistoryDB
from .logging_utils import append_log
from .maest import DEFAULT_MODEL, DEFAULT_MODEL_REVISION
from .performance import (
    append_perf,
    average_seconds,
    clock,
    elapsed_seconds,
    milliseconds,
    tracks_per_minute,
)
from .presentation import format_result_text
from .profile_analyzer import ProfileAnalyzer
from .report import write_json, write_summary_csv
from .runtime_diagnostics import collect_runtime_diagnostics
from .runtime_meta import default_history_path, default_log_path, default_results_dir
from .validation_gui import ValidationTab

AUDIO_FILETYPES = [
    ("Audio files", "*.wav *.flac *.mp3 *.ogg *.m4a *.aac"),
    ("All files", "*.*"),
]

MODE_LABELS = {
    "Авто": "auto",
    "Быстрый": "fast",
    "Точный": "accurate",
    "Экспертный": "expert",
}

VIEW_LABELS = {
    "Авто (все)": "all",
    "Обычный": "normal",
    "SUNO": "suno",
    "Дистрибьютор": "distributor",
}

SEPARATOR = "=" * 88


@dataclass(frozen=True)
class LiveAnalysisSettings:
    device: str
    mode: str
    view: str
    include_path: bool


class GenreTestWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"Genre_test v{__version__} — Music Genre Analyzer")
        self.geometry("1180x840")
        self.minsize(900, 650)

        self.input_var = tk.StringVar()
        self.out_var = tk.StringVar(value=str(default_results_dir()))
        self.device_var = tk.StringVar(value="auto")
        self.mode_var = tk.StringVar(value="Авто")
        self.view_var = tk.StringVar(value="Авто (все)")
        self.full_path_var = tk.BooleanVar(value=False)
        self.windows_var = tk.IntVar(value=5)
        self.top_k_var = tk.IntVar(value=15)
        self.status_var = tk.StringVar(value="Готов")
        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._cancel_event = threading.Event()
        self._busy = False
        self._settings_lock = threading.Lock()
        self._live_settings = LiveAnalysisSettings(
            device="auto",
            mode="auto",
            view="all",
            include_path=False,
        )
        self.runtime_diagnostics = collect_runtime_diagnostics()

        self._build_ui()
        append_log(
            f"GUI started: Genre_test {__version__}; MAEST revision={DEFAULT_MODEL_REVISION}; "
            f"FFmpeg={self.runtime_diagnostics.ffmpeg_path or 'MISSING'}"
        )
        self.after(120, self._poll_queue)

    def _build_ui(self) -> None:
        runtime_bar = ttk.Frame(self, padding=(10, 6))
        runtime_bar.pack(fill="x")
        ttk.Label(
            runtime_bar,
            text=f"Genre_test {__version__} | MAEST revision: {DEFAULT_MODEL_REVISION}",
        ).pack(side="left")
        warning = self.runtime_diagnostics.decoder_warning
        if warning:
            tk.Label(
                runtime_bar,
                text=warning,
                fg="#b00020",
                font=("Segoe UI", 9, "bold"),
            ).pack(side="right", padx=(12, 0))
        else:
            ttk.Label(runtime_bar, text="FFmpeg: OK").pack(side="right", padx=(12, 0))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        analysis_tab = ttk.Frame(notebook, padding=12)
        validation_tab = ValidationTab(notebook)
        notebook.add(analysis_tab, text="Анализ")
        notebook.add(validation_tab, text="Validation / Перепроверка")

        root = analysis_tab
        root.columnconfigure(1, weight=1)
        root.rowconfigure(5, weight=1)

        ttk.Label(root, text="Вход:").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(root, textvariable=self.input_var).grid(
            row=0, column=1, sticky="ew", padx=(8, 8), pady=4
        )
        ttk.Button(root, text="Выбрать файл", command=self._choose_file).grid(
            row=0, column=2, padx=3, pady=4
        )
        ttk.Button(root, text="Выбрать папку", command=self._choose_folder).grid(
            row=0, column=3, padx=3, pady=4
        )

        ttk.Label(root, text="Результаты:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(root, textvariable=self.out_var).grid(
            row=1, column=1, sticky="ew", padx=(8, 8), pady=4
        )
        ttk.Button(root, text="Выбрать", command=self._choose_output).grid(
            row=1, column=2, padx=3, pady=4
        )
        ttk.Button(root, text="Открыть", command=self._open_output).grid(
            row=1, column=3, padx=3, pady=4
        )

        settings = ttk.Frame(root)
        settings.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(8, 4))
        ttk.Label(settings, text="Device").pack(side="left")
        device_combo = ttk.Combobox(
            settings,
            textvariable=self.device_var,
            values=("auto", "cuda", "cpu"),
            state="readonly",
            width=8,
        )
        device_combo.pack(side="left", padx=(6, 18))
        device_combo.bind("<<ComboboxSelected>>", self._on_live_setting_changed)

        ttk.Label(settings, text="Режим анализа").pack(side="left")
        mode_combo = ttk.Combobox(
            settings,
            textvariable=self.mode_var,
            values=tuple(MODE_LABELS),
            state="readonly",
            width=13,
        )
        mode_combo.pack(side="left", padx=(6, 18))
        mode_combo.bind("<<ComboboxSelected>>", self._on_mode_selected)

        ttk.Label(settings, text="Вывод").pack(side="left")
        view_combo = ttk.Combobox(
            settings,
            textvariable=self.view_var,
            values=tuple(VIEW_LABELS),
            state="readonly",
            width=17,
        )
        view_combo.pack(side="left", padx=(6, 12))
        view_combo.bind("<<ComboboxSelected>>", self._on_live_setting_changed)

        ttk.Checkbutton(
            settings,
            text="Полный путь",
            variable=self.full_path_var,
            command=self._on_live_setting_changed,
        ).pack(side="left", padx=(0, 12))

        self.advanced_frame = ttk.Frame(settings)
        ttk.Label(self.advanced_frame, text="Окон").pack(side="left")
        ttk.Spinbox(
            self.advanced_frame,
            from_=1,
            to=12,
            textvariable=self.windows_var,
            width=5,
        ).pack(side="left", padx=(6, 12))
        ttk.Label(self.advanced_frame, text="Top-K").pack(side="left")
        ttk.Spinbox(
            self.advanced_frame,
            from_=3,
            to=50,
            textvariable=self.top_k_var,
            width=5,
        ).pack(side="left", padx=(6, 0))

        actions = ttk.Frame(root)
        actions.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(8, 6))
        self.run_button = ttk.Button(actions, text="АНАЛИЗИРОВАТЬ", command=self._start)
        self.run_button.pack(side="left")
        self.stop_button = ttk.Button(
            actions,
            text="ОСТАНОВИТЬ",
            command=self._request_stop,
            state="disabled",
        )
        self.stop_button.pack(side="left", padx=(8, 0))
        self.progress = ttk.Progressbar(actions, mode="indeterminate", length=220)
        self.progress.pack(side="left", padx=14)
        ttk.Label(actions, textvariable=self.status_var).pack(side="left")
        ttk.Label(actions, text=f"History: {default_history_path()}").pack(side="right")

        ttk.Separator(root).grid(row=4, column=0, columnspan=4, sticky="ew", pady=6)
        self.output = tk.Text(root, wrap="none", font=("Consolas", 10), undo=False)
        self.output.grid(row=5, column=0, columnspan=4, sticky="nsew")
        bind_copy_shortcuts(self.output)
        yscroll = ttk.Scrollbar(root, orient="vertical", command=self.output.yview)
        yscroll.grid(row=5, column=4, sticky="ns")
        xscroll = ttk.Scrollbar(root, orient="horizontal", command=self.output.xview)
        xscroll.grid(row=6, column=0, columnspan=4, sticky="ew")
        self.output.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        footer = ttk.Frame(root)
        footer.grid(row=7, column=0, columnspan=4, sticky="ew", pady=(6, 0))
        ttk.Button(
            footer,
            text="СКОПИРОВАТЬ СОДЕРЖИМОЕ",
            command=self._copy_output,
        ).pack(side="left")
        log_link = tk.Label(
            footer,
            text=f"Лог: {default_log_path()}",
            fg="#0563c1",
            cursor="hand2",
            font=("Segoe UI", 9, "underline"),
            takefocus=True,
        )
        log_link.pack(side="left", padx=(12, 0))
        log_link.bind("<Button-1>", self._open_log_folder)
        log_link.bind("<Return>", self._open_log_folder)
        log_link.bind("<space>", self._open_log_folder)
        self._sync_mode_ui()
        self._publish_live_settings(notify=False)

    def _sync_mode_ui(self) -> None:
        if MODE_LABELS.get(self.mode_var.get()) == "expert":
            if not self.advanced_frame.winfo_manager():
                self.advanced_frame.pack(side="left")
        elif self.advanced_frame.winfo_manager():
            self.advanced_frame.pack_forget()

    def _on_mode_selected(self, _event=None) -> None:
        self._sync_mode_ui()
        self._publish_live_settings()

    def _on_live_setting_changed(self, _event=None) -> None:
        self._publish_live_settings()

    def _publish_live_settings(self, *, notify: bool = True) -> None:
        settings = LiveAnalysisSettings(
            device=self.device_var.get(),
            mode=MODE_LABELS.get(self.mode_var.get(), "auto"),
            view=VIEW_LABELS.get(self.view_var.get(), "all"),
            include_path=bool(self.full_path_var.get()),
        )
        with self._settings_lock:
            previous = self._live_settings
            self._live_settings = settings

        if not notify or not self._busy or settings == previous:
            return

        analysis_changed = settings.device != previous.device or settings.mode != previous.mode
        presentation_changed = (
            settings.view != previous.view or settings.include_path != previous.include_path
        )
        if analysis_changed and presentation_changed:
            message = "Настройки изменены: анализ — со следующего трека, вывод — с ближайшего результата"
        elif analysis_changed:
            message = "Device/режим изменены — применятся со следующего трека"
        else:
            message = "Тип вывода изменён — применится к ближайшему результату"
        self.status_var.set(message)
        append_log(
            "Live settings changed: "
            f"device={settings.device}; mode={settings.mode}; view={settings.view}; "
            f"include_path={settings.include_path}; analysis_applies=next_track"
        )

    def _snapshot_live_settings(self) -> LiveAnalysisSettings:
        with self._settings_lock:
            return self._live_settings

    def _choose_file(self) -> None:
        selected = filedialog.askopenfilename(
            title="Выберите аудиофайл",
            filetypes=AUDIO_FILETYPES,
        )
        if selected:
            self.input_var.set(selected)

    def _choose_folder(self) -> None:
        selected = filedialog.askdirectory(title="Выберите папку с аудиофайлами")
        if selected:
            self.input_var.set(selected)

    def _choose_output(self) -> None:
        selected = filedialog.askdirectory(title="Папка результатов")
        if selected:
            self.out_var.set(selected)

    def _open_output(self) -> None:
        out = Path(self.out_var.get()).expanduser()
        out.mkdir(parents=True, exist_ok=True)
        os.startfile(out)  # type: ignore[attr-defined]

    def _open_log_folder(self, _event=None) -> None:
        path = default_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
        os.startfile(path.parent)  # type: ignore[attr-defined]

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
            self.output.insert("end", f"\n\n{SEPARATOR}\n\n")
        self.output.insert("end", text.rstrip() + "\n")
        self.output.see("end")
        self.output.update_idletasks()

    def _start(self) -> None:
        if self._busy:
            return
        source = Path(self.input_var.get().strip().strip('"')).expanduser()
        if not source.exists():
            messagebox.showerror(
                "Genre_test",
                "Выберите существующий аудиофайл или папку.",
            )
            return
        out = Path(self.out_var.get().strip().strip('"')).expanduser()
        self._publish_live_settings(notify=False)
        settings = self._snapshot_live_settings()
        windows = self.windows_var.get()
        top_k = self.top_k_var.get()
        self.output.delete("1.0", "end")
        self._append_output(
            f"Источник: {source}\n"
            f"Device: {settings.device}\n"
            f"Режим: {settings.mode}\n"
            f"Вывод: {settings.view}\n"
            f"Полный путь: {'да' if settings.include_path else 'нет'}\n"
            "Профиль: MAEST + AudioSet AST\nПодготовка анализа…"
        )
        self._cancel_event.clear()
        self._busy = True
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.progress.start(10)
        self.status_var.set("Загрузка моделей / анализ…")
        append_log(
            f"Analysis started: source={source}; device={settings.device}; mode={settings.mode}; "
            f"view={settings.view}; include_path={settings.include_path}; output={out}"
        )
        threading.Thread(
            target=self._worker,
            args=(source, out, windows, top_k),
            daemon=True,
        ).start()

    def _request_stop(self) -> None:
        if not self._busy or self._cancel_event.is_set():
            return
        self._cancel_event.set()
        self.stop_button.configure(state="disabled")
        self.status_var.set("Остановка после текущего безопасного шага…")
        append_log("Safe stop requested by user")

    @staticmethod
    def _make_analyzer(
        settings: LiveAnalysisSettings,
        windows: int,
        top_k: int,
    ) -> ProfileAnalyzer:
        return ProfileAnalyzer(
            model_id=DEFAULT_MODEL,
            device=settings.device,
            analysis_mode=settings.mode,
            window_count=windows,
            top_k=top_k,
            semantic_mode="auto",
        )

    def _worker(
        self,
        source: Path,
        out: Path,
        windows: int,
        top_k: int,
    ) -> None:
        session_started = clock()
        results: list = []
        file_errors: list[str] = []
        processing_started: float | None = None
        try:
            history = HistoryDB()
            processing_started = clock()
            if source.is_file():
                analysis_settings = self._snapshot_live_settings()
                analyzer = self._make_analyzer(analysis_settings, windows, top_k)
                item_started = clock()
                result = analyzer.analyze(
                    source,
                    analysis_mode=analysis_settings.mode,
                    cancel_check=self._cancel_event.is_set,
                )
                write_json(result, out)
                history.record_result(result)
                item_s = elapsed_seconds(item_started)
                total_s = elapsed_seconds(session_started)
                render_settings = self._snapshot_live_settings()
                append_perf(
                    "analysis_item",
                    path=source,
                    status="ok",
                    mode=result.analysis_mode,
                    requested_device=analysis_settings.device,
                    profile_view=render_settings.view,
                    semantic_status=(
                        result.semantic_evidence.status if result.semantic_evidence else "not_available"
                    ),
                    elapsed_ms=milliseconds(item_s),
                    includes_persistence=True,
                )
                append_perf(
                    "analysis_session",
                    source=source,
                    status="complete",
                    completed=1,
                    errors=0,
                    total_ms=milliseconds(total_s),
                    processing_ms=milliseconds(elapsed_seconds(processing_started)),
                    avg_seconds_per_track=average_seconds(1, item_s),
                    tracks_per_minute=tracks_per_minute(1, item_s),
                )
                text = format_result_text(
                    result,
                    view=render_settings.view,
                    include_path=render_settings.include_path,
                ) + f"\n\nElapsed: {item_s:.2f} s"
                append_log(f"Analysis complete: {source}; elapsed={item_s:.3f}s")
                self._queue.put(("done", text))
                return

            files = iter_audio_files(source)
            if not files:
                raise RuntimeError(
                    "В выбранной папке не найдено поддерживаемых аудиофайлов."
                )
            self._queue.put(("append", f"Найдено аудиофайлов: {len(files)}"))
            analyzer: ProfileAnalyzer | None = None
            analyzer_device: str | None = None

            for idx, path in enumerate(files, 1):
                if self._cancel_event.is_set():
                    raise AnalysisCancelled("Operation cancelled by user")

                analysis_settings = self._snapshot_live_settings()
                if analyzer is None or analyzer_device != analysis_settings.device:
                    analyzer = self._make_analyzer(analysis_settings, windows, top_k)
                    analyzer_device = analysis_settings.device
                    append_log(
                        f"Batch analyzer prepared: device={analysis_settings.device}; "
                        f"mode={analysis_settings.mode}"
                    )

                self._queue.put(
                    (
                        "status",
                        f"[{idx}/{len(files)}] {path.name} | "
                        f"{analysis_settings.device} | {analysis_settings.mode}",
                    )
                )
                item_started = clock()
                try:
                    result = analyzer.analyze(
                        path,
                        analysis_mode=analysis_settings.mode,
                        cancel_check=self._cancel_event.is_set,
                    )
                except AnalysisCancelled:
                    raise
                except Exception as exc:
                    item_s = elapsed_seconds(item_started)
                    detail = traceback.format_exc()
                    summary = f"[ERROR] {path.name}: {type(exc).__name__}: {exc}"
                    file_errors.append(summary)
                    append_log(f"Batch file failed: {path}\n{detail}")
                    append_perf(
                        "analysis_item",
                        path=path,
                        status="error",
                        mode=analysis_settings.mode,
                        requested_device=analysis_settings.device,
                        elapsed_ms=milliseconds(item_s),
                        error_type=type(exc).__name__,
                    )
                    self._queue.put(("append_block", summary))
                    continue

                results.append(result)
                write_json(result, out)
                history.record_result(result)
                item_s = elapsed_seconds(item_started)
                render_settings = self._snapshot_live_settings()
                append_perf(
                    "analysis_item",
                    path=path,
                    status="ok",
                    mode=result.analysis_mode,
                    requested_device=analysis_settings.device,
                    profile_view=render_settings.view,
                    semantic_status=(
                        result.semantic_evidence.status if result.semantic_evidence else "not_available"
                    ),
                    elapsed_ms=milliseconds(item_s),
                    includes_persistence=True,
                )
                block = format_result_text(
                    result,
                    top_n=5,
                    view=render_settings.view,
                    include_path=render_settings.include_path,
                ) + f"\nElapsed: {item_s:.2f} s"
                self._queue.put(("append_block", block))

            summary_csv = write_summary_csv(results, out) if results else None
            total_s = elapsed_seconds(session_started)
            processing_s = (
                elapsed_seconds(processing_started) if processing_started is not None else total_s
            )
            avg_s = average_seconds(len(results), processing_s)
            rate = tracks_per_minute(len(results), processing_s)
            semantic_ok = sum(
                result.semantic_evidence is not None and result.semantic_evidence.status == "ok"
                for result in results
            )
            summary = (
                f"Completed: {len(results)} / {len(files)}\n"
                f"Semantic profiles: {semantic_ok} / {len(results)}\n"
                f"File errors skipped: {len(file_errors)}\n"
                f"Elapsed: {total_s:.2f} s\n"
                f"Processing: {processing_s:.2f} s\n"
                f"Average: {avg_s:.3f} s/track\n"
                f"Throughput: {rate:.3f} tracks/min"
            )
            if summary_csv:
                summary += f"\nSummary CSV: {summary_csv}"
            append_log(
                f"Batch complete: source={source}; completed={len(results)}; "
                f"semantic_ok={semantic_ok}; errors={len(file_errors)}; elapsed={total_s:.3f}s; "
                f"throughput={rate:.3f} tracks/min"
            )
            append_perf(
                "analysis_session",
                source=source,
                status="complete",
                files_seen=len(files),
                completed=len(results),
                semantic_ok=semantic_ok,
                errors=len(file_errors),
                total_ms=milliseconds(total_s),
                processing_ms=milliseconds(processing_s),
                avg_seconds_per_track=avg_s,
                tracks_per_minute=rate,
            )
            self._queue.put(("done", summary))
        except AnalysisCancelled:
            if results:
                write_summary_csv(results, out)
            total_s = elapsed_seconds(session_started)
            processing_s = (
                elapsed_seconds(processing_started) if processing_started is not None else total_s
            )
            avg_s = average_seconds(len(results), processing_s)
            rate = tracks_per_minute(len(results), processing_s)
            message = (
                "Остановлено пользователем безопасно.\n"
                f"Полностью завершённых треков сохранено: {len(results)}.\n"
                f"Ошибочных файлов пропущено: {len(file_errors)}.\n"
                f"Время до остановки: {total_s:.2f} s.\n"
                f"Среднее: {avg_s:.3f} s/track; {rate:.3f} tracks/min.\n"
                "Текущий незавершённый трек в историю не записан."
            )
            append_log(
                f"Analysis stopped safely: completed={len(results)}; errors={len(file_errors)}; "
                f"elapsed={total_s:.3f}s"
            )
            append_perf(
                "analysis_session",
                source=source,
                status="stopped",
                completed=len(results),
                errors=len(file_errors),
                total_ms=milliseconds(total_s),
                processing_ms=milliseconds(processing_s),
                avg_seconds_per_track=avg_s,
                tracks_per_minute=rate,
            )
            self._queue.put(("cancelled", message))
        except Exception:
            total_s = elapsed_seconds(session_started)
            detail = traceback.format_exc()
            append_log(f"Analysis fatal error after {total_s:.3f}s:\n{detail}")
            append_perf(
                "analysis_session",
                source=source,
                status="fatal_error",
                completed=len(results),
                errors=len(file_errors),
                total_ms=milliseconds(total_s),
            )
            self._queue.put(("error", detail))

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "status":
                    self.status_var.set(str(payload))
                elif kind == "append":
                    self._append_output(str(payload))
                elif kind == "append_block":
                    self._append_output(str(payload), separator=True)
                elif kind == "done":
                    self._append_output(str(payload), separator=True)
                    self._finish("Готово")
                elif kind == "cancelled":
                    self._append_output(str(payload), separator=True)
                    self._finish("Остановлено")
                elif kind == "error":
                    self._append_output(str(payload), separator=True)
                    self._finish("Ошибка")
                    messagebox.showerror(
                        "Genre_test",
                        "Анализ завершился ошибкой. Подробности в окне и журнале.",
                    )
        except queue.Empty:
            pass
        self.after(120, self._poll_queue)

    def _finish(self, status: str) -> None:
        self._busy = False
        self.progress.stop()
        self.run_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status_var.set(status)


def main() -> None:
    GenreTestWindow().mainloop()


if __name__ == "__main__":
    main()
