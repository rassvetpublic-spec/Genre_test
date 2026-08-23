from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
import traceback
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .analyzer import GenreAnalyzer
from .audio import iter_audio_files
from .maest import DEFAULT_MODEL
from .presentation import format_result_text
from .report import write_json, write_summary_csv

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


class GenreTestWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"Genre_test v{__version__} — Music Genre Analyzer")
        self.geometry("920x680")
        self.minsize(760, 560)

        self.input_var = tk.StringVar()
        self.out_var = tk.StringVar(value=str((Path.cwd() / "results").resolve()))
        self.device_var = tk.StringVar(value="auto")
        self.mode_var = tk.StringVar(value="Авто")
        self.windows_var = tk.IntVar(value=5)
        self.top_k_var = tk.IntVar(value=15)
        self.status_var = tk.StringVar(value="Готов")
        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._busy = False

        self._build_ui()
        self.after(120, self._poll_queue)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
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
        ttk.Combobox(
            settings,
            textvariable=self.device_var,
            values=("auto", "cuda", "cpu"),
            state="readonly",
            width=8,
        ).pack(side="left", padx=(6, 18))

        ttk.Label(settings, text="Режим анализа").pack(side="left")
        mode_combo = ttk.Combobox(
            settings,
            textvariable=self.mode_var,
            values=tuple(MODE_LABELS),
            state="readonly",
            width=13,
        )
        mode_combo.pack(side="left", padx=(6, 18))
        mode_combo.bind("<<ComboboxSelected>>", self._sync_mode_ui)

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
        self.progress = ttk.Progressbar(actions, mode="indeterminate", length=220)
        self.progress.pack(side="left", padx=14)
        ttk.Label(actions, textvariable=self.status_var).pack(side="left")

        ttk.Separator(root).grid(row=4, column=0, columnspan=4, sticky="ew", pady=6)
        self.output = tk.Text(root, wrap="none", font=("Consolas", 10), undo=False)
        self.output.grid(row=5, column=0, columnspan=4, sticky="nsew")
        yscroll = ttk.Scrollbar(root, orient="vertical", command=self.output.yview)
        yscroll.grid(row=5, column=4, sticky="ns")
        xscroll = ttk.Scrollbar(root, orient="horizontal", command=self.output.xview)
        xscroll.grid(row=6, column=0, columnspan=4, sticky="ew")
        self.output.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        self._sync_mode_ui()

    def _sync_mode_ui(self, _event=None) -> None:
        if MODE_LABELS.get(self.mode_var.get()) == "expert":
            if not self.advanced_frame.winfo_manager():
                self.advanced_frame.pack(side="left")
        elif self.advanced_frame.winfo_manager():
            self.advanced_frame.pack_forget()

    def _choose_file(self) -> None:
        selected = filedialog.askopenfilename(title="Выберите аудиофайл", filetypes=AUDIO_FILETYPES)
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

    def _start(self) -> None:
        if self._busy:
            return
        source = Path(self.input_var.get().strip().strip('"')).expanduser()
        if not source.exists():
            messagebox.showerror("Genre_test", "Выберите существующий аудиофайл или папку.")
            return
        out = Path(self.out_var.get().strip().strip('"')).expanduser()
        mode = MODE_LABELS.get(self.mode_var.get(), "auto")
        self.output.delete("1.0", "end")
        self._busy = True
        self.run_button.configure(state="disabled")
        self.progress.start(10)
        self.status_var.set("Загрузка модели / анализ…")

        thread = threading.Thread(
            target=self._worker,
            args=(
                source,
                out,
                self.device_var.get(),
                mode,
                self.windows_var.get(),
                self.top_k_var.get(),
            ),
            daemon=True,
        )
        thread.start()

    def _worker(
        self,
        source: Path,
        out: Path,
        device: str,
        mode: str,
        windows: int,
        top_k: int,
    ) -> None:
        try:
            analyzer = GenreAnalyzer(
                model_id=DEFAULT_MODEL,
                device=device,
                analysis_mode=mode,
                window_count=windows,
                top_k=top_k,
            )
            if source.is_file():
                result = analyzer.analyze(source)
                target = write_json(result, out)
                text = format_result_text(result) + f"\n\nJSON: {target}"
                self._queue.put(("done", text))
                return

            files = iter_audio_files(source)
            if not files:
                raise RuntimeError("В выбранной папке не найдено поддерживаемых аудиофайлов.")
            results = []
            blocks = []
            for idx, path in enumerate(files, 1):
                self._queue.put(("status", f"[{idx}/{len(files)}] {path.name}"))
                result = analyzer.analyze(path)
                results.append(result)
                write_json(result, out)
                blocks.append(format_result_text(result, top_n=5))
            csv_path = write_summary_csv(results, out)
            blocks.append(f"Summary CSV: {csv_path}")
            self._queue.put(("done", "\n\n" + ("\n\n" + "=" * 72 + "\n\n").join(blocks)))
        except Exception:
            self._queue.put(("error", traceback.format_exc()))

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "status":
                    self.status_var.set(str(payload))
                elif kind == "done":
                    self.output.insert("end", str(payload).lstrip())
                    self.output.see("1.0")
                    self._finish("Готово")
                elif kind == "error":
                    self.output.insert("end", str(payload))
                    self._finish("Ошибка")
                    messagebox.showerror("Genre_test", "Анализ завершился ошибкой. Подробности в окне.")
        except queue.Empty:
            pass
        self.after(120, self._poll_queue)

    def _finish(self, status: str) -> None:
        self._busy = False
        self.progress.stop()
        self.run_button.configure(state="normal")
        self.status_var.set(status)


def main() -> None:
    GenreTestWindow().mainloop()


if __name__ == "__main__":
    main()
