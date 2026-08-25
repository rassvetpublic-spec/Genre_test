from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from . import __version__
from .logging_utils import append_log
from .runtime_health import RuntimeHealth, collect_runtime_health

STATUS_COLORS = {
    "OK": "#187a2f",
    "WARN": "#a35b00",
    "FAIL": "#b00020",
}

EXPERT_WINDOWS_MIN = 1
EXPERT_WINDOWS_MAX = 12
EXPERT_TOP_K_MIN = 3
EXPERT_TOP_K_MAX = 50
EXPERT_WINDOWS_DEFAULT = 5
EXPERT_TOP_K_DEFAULT = 15


def _blocking_failure(health: RuntimeHealth) -> bool:
    return any(
        item.status == "FAIL" and item.category in {"Core", "Package"}
        for item in health.components
    )


def _cuda_usable(health: RuntimeHealth) -> bool:
    cuda = health.by_name("CUDA")
    return bool(cuda and cuda.status == "OK" and cuda.value != "unavailable")


def _device_options(health: RuntimeHealth) -> tuple[str, ...]:
    if _cuda_usable(health):
        return ("auto", "cuda", "cpu")
    return ("auto", "cpu")


def _bounded_expert_parameters(window_count: int, top_k: int) -> tuple[int, int]:
    return (
        min(EXPERT_WINDOWS_MAX, max(EXPERT_WINDOWS_MIN, window_count)),
        min(EXPERT_TOP_K_MAX, max(EXPERT_TOP_K_MIN, top_k)),
    )


def _find_bound_combobox(root: tk.Misc, variable: tk.Variable) -> ttk.Combobox | None:
    target = str(variable)
    stack: list[tk.Misc] = [root]
    while stack:
        parent = stack.pop()
        for child in parent.winfo_children():
            stack.append(child)
            if isinstance(child, ttk.Combobox) and str(child.cget("textvariable")) == target:
                return child
    return None


def _is_device_selector_values(values: tuple[str, ...]) -> bool:
    normalized = set(values)
    return {"auto", "cpu"}.issubset(normalized) and normalized.issubset(
        {"auto", "cuda", "cpu"}
    )


def _find_device_comboboxes(root: tk.Misc) -> list[ttk.Combobox]:
    matches: list[ttk.Combobox] = []
    stack: list[tk.Misc] = [root]
    while stack:
        parent = stack.pop()
        for child in parent.winfo_children():
            stack.append(child)
            if not isinstance(child, ttk.Combobox):
                continue
            values = tuple(str(value) for value in child.cget("values"))
            if _is_device_selector_values(values):
                matches.append(child)
    return matches


def _fill_tree(tree: ttk.Treeview, health: RuntimeHealth) -> None:
    for item_id in tree.get_children():
        tree.delete(item_id)
    for component in health.components:
        tree.insert(
            "",
            "end",
            values=(
                component.category,
                component.name,
                component.status,
                component.value,
                component.details,
            ),
            tags=(component.status,),
        )


def _configure_tree_tags(tree: ttk.Treeview) -> None:
    tree.tag_configure("OK", foreground=STATUS_COLORS["OK"])
    tree.tag_configure("WARN", foreground=STATUS_COLORS["WARN"])
    tree.tag_configure("FAIL", foreground=STATUS_COLORS["FAIL"])


def _build_health_tree(parent: tk.Misc) -> ttk.Treeview:
    columns = ("category", "component", "status", "value", "details")
    tree = ttk.Treeview(parent, columns=columns, show="headings", height=18)
    tree.heading("category", text="Группа")
    tree.heading("component", text="Компонент")
    tree.heading("status", text="Статус")
    tree.heading("value", text="Версия / значение")
    tree.heading("details", text="Подробности")
    tree.column("category", width=95, stretch=False)
    tree.column("component", width=155, stretch=False)
    tree.column("status", width=70, stretch=False, anchor="center")
    tree.column("value", width=280, stretch=True)
    tree.column("details", width=360, stretch=True)
    _configure_tree_tags(tree)
    return tree


def _show_blocking_failure(health: RuntimeHealth) -> None:
    root = tk.Tk()
    root.title(f"Genre_test v{__version__} — Runtime dependency error")
    root.geometry("960x580")
    root.minsize(780, 440)

    header = tk.Label(
        root,
        text="Genre_test не может запустить основной GUI: отсутствует обязательная зависимость",
        fg=STATUS_COLORS["FAIL"],
        font=("Segoe UI", 10, "bold"),
        padx=12,
        pady=10,
    )
    header.pack(fill="x")

    frame = ttk.Frame(root, padding=(10, 0, 10, 10))
    frame.pack(fill="both", expand=True)
    tree = _build_health_tree(frame)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    scrollbar.pack(side="right", fill="y")
    tree.configure(yscrollcommand=scrollbar.set)
    _fill_tree(tree, health)

    footer = ttk.Frame(root, padding=10)
    footer.pack(fill="x")
    ttk.Label(footer, text="Запустите .\\scripts\\upgrade.ps1 и повторите проверку.").pack(
        side="left"
    )
    ttk.Button(footer, text="Закрыть", command=root.destroy).pack(side="right")
    root.mainloop()


def main() -> None:
    initial_health = collect_runtime_health()
    if _blocking_failure(initial_health):
        _show_blocking_failure(initial_health)
        return

    from .gui import GenreTestWindow

    class RuntimeHealthWindow(GenreTestWindow):
        def __init__(self) -> None:
            self.runtime_health = initial_health
            self._health_bar: ttk.Frame | None = None
            self._health_summary_label: tk.Label | None = None
            super().__init__()
            append_log(
                f"Runtime health: overall={self.runtime_health.overall_status}; "
                f"{self.runtime_health.compact_summary}"
            )

        def _publish_live_settings(self, *, notify: bool = True) -> None:
            if self.device_var.get() == "cuda" and not _cuda_usable(self.runtime_health):
                self.device_var.set("auto")
                super()._publish_live_settings(notify=False)
                if notify:
                    self.status_var.set("CUDA недоступна — Device оставлен auto (CPU fallback)")
                    append_log(
                        "Rejected live device change: cuda unavailable; device reset to auto"
                    )
                return
            super()._publish_live_settings(notify=notify)

        def _sync_device_capability(self) -> None:
            options = _device_options(self.runtime_health)
            for combo in _find_device_comboboxes(self):
                combo.configure(values=options)
                if combo.get() not in options:
                    combo.set("auto")
            if self.device_var.get() == "cuda" and not _cuda_usable(self.runtime_health):
                self.device_var.set("auto")
                super()._publish_live_settings(notify=False)

        def _normalize_expert_inputs(self) -> None:
            changed = False
            try:
                windows = int(self.windows_var.get())
            except (tk.TclError, TypeError, ValueError):
                windows = EXPERT_WINDOWS_DEFAULT
                changed = True
            try:
                top_k = int(self.top_k_var.get())
            except (tk.TclError, TypeError, ValueError):
                top_k = EXPERT_TOP_K_DEFAULT
                changed = True

            bounded_windows, bounded_top_k = _bounded_expert_parameters(windows, top_k)
            changed = changed or bounded_windows != windows or bounded_top_k != top_k
            self.windows_var.set(bounded_windows)
            self.top_k_var.set(bounded_top_k)

            if changed:
                self.status_var.set(
                    f"Параметры Expert скорректированы: Окон={bounded_windows}, "
                    f"Top-K={bounded_top_k}"
                )
                append_log(
                    "Expert parameters normalized before analysis: "
                    f"windows={bounded_windows}; top_k={bounded_top_k}"
                )

        def _start(self) -> None:
            self._normalize_expert_inputs()
            super()._start()

        def _build_ui(self) -> None:
            super()._build_ui()
            self._sync_device_capability()
            children = self.winfo_children()
            old_runtime_bar = children[0] if children else None
            notebook = next((child for child in children if isinstance(child, ttk.Notebook)), None)
            if old_runtime_bar is not None and old_runtime_bar is not notebook:
                old_runtime_bar.pack_forget()
            self._health_bar = ttk.Frame(self, padding=(10, 6))
            if notebook is not None:
                self._health_bar.pack(fill="x", before=notebook)
            else:
                self._health_bar.pack(fill="x")
            self._render_health_bar()

        def _render_health_bar(self) -> None:
            assert self._health_bar is not None
            for child in self._health_bar.winfo_children():
                child.destroy()

            ttk.Label(
                self._health_bar,
                text=f"Genre_test {__version__} | Models: MAEST Discogs519 + AudioSet AST",
            ).pack(side="left")

            ttk.Button(
                self._health_bar,
                text="Зависимости…",
                command=self._show_runtime_health,
            ).pack(side="right", padx=(10, 0))

            overall = self.runtime_health.overall_status
            self._health_summary_label = tk.Label(
                self._health_bar,
                text=f"Runtime: {overall} | {self.runtime_health.compact_summary}",
                fg=STATUS_COLORS[overall],
                font=("Segoe UI", 9, "bold" if overall != "OK" else "normal"),
            )
            self._health_summary_label.pack(side="right")

        def _refresh_runtime_health(self, tree: ttk.Treeview, summary: tk.Label) -> None:
            self.runtime_health = collect_runtime_health()
            self._sync_device_capability()
            _fill_tree(tree, self.runtime_health)
            overall = self.runtime_health.overall_status
            summary.configure(
                text=f"Runtime: {overall} | {self.runtime_health.compact_summary}",
                fg=STATUS_COLORS[overall],
            )
            self._render_health_bar()
            append_log(
                f"Runtime health refreshed: overall={overall}; "
                f"{self.runtime_health.compact_summary}"
            )

        def _show_runtime_health(self) -> None:
            dialog = tk.Toplevel(self)
            dialog.title(f"Genre_test v{__version__} — Runtime / Dependencies")
            dialog.geometry("1020x620")
            dialog.minsize(820, 460)
            dialog.transient(self)

            header = ttk.Frame(dialog, padding=(10, 10, 10, 6))
            header.pack(fill="x")
            overall = self.runtime_health.overall_status
            summary = tk.Label(
                header,
                text=f"Runtime: {overall} | {self.runtime_health.compact_summary}",
                fg=STATUS_COLORS[overall],
                font=("Segoe UI", 10, "bold"),
            )
            summary.pack(side="left")
            ttk.Button(
                header,
                text="Обновить",
                command=lambda: self._refresh_runtime_health(tree, summary),
            ).pack(side="right")

            body = ttk.Frame(dialog, padding=(10, 0, 10, 6))
            body.pack(fill="both", expand=True)
            tree = _build_health_tree(body)
            tree.pack(side="left", fill="both", expand=True)
            scrollbar = ttk.Scrollbar(body, orient="vertical", command=tree.yview)
            scrollbar.pack(side="right", fill="y")
            tree.configure(yscrollcommand=scrollbar.set)
            _fill_tree(tree, self.runtime_health)

            legend = ttk.Label(
                dialog,
                text=(
                    "OK — компонент доступен   |   WARN — есть fallback/ограничение   |   "
                    "FAIL — обязательный компонент отсутствует или не запускается"
                ),
                padding=(10, 4),
            )
            legend.pack(fill="x")
            footer = ttk.Frame(dialog, padding=(10, 4, 10, 10))
            footer.pack(fill="x")
            ttk.Button(footer, text="Закрыть", command=dialog.destroy).pack(side="right")

    RuntimeHealthWindow().mainloop()


if __name__ == "__main__":
    main()
