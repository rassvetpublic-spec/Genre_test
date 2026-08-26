from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .resource_monitor_gui import ResourceMonitorWindow

RESOURCE_BUTTON_TEXT = "Ресурсы…"
DEPENDENCY_BUTTON_TEXT = "Зависимости…"


def _find_health_bar(root: tk.Misc) -> tuple[ttk.Frame, ttk.Button] | None:
    stack: list[tk.Misc] = [root]
    while stack:
        parent = stack.pop()
        for child in parent.winfo_children():
            stack.append(child)
            if not isinstance(child, ttk.Frame):
                continue
            dependency_button = next(
                (
                    nested
                    for nested in child.winfo_children()
                    if isinstance(nested, ttk.Button)
                    and str(nested.cget("text")) == DEPENDENCY_BUTTON_TEXT
                ),
                None,
            )
            if dependency_button is not None:
                return child, dependency_button
    return None


def _show_resource_monitor(root: tk.Misc) -> None:
    existing = getattr(root, "_genre_test_resource_monitor_window", None)
    try:
        if existing is not None and bool(existing.winfo_exists()):
            existing.deiconify()
            existing.lift()
            existing.focus_force()
            return
    except tk.TclError:
        pass

    window = ResourceMonitorWindow(root)
    setattr(root, "_genre_test_resource_monitor_window", window)


def install_resource_monitor_button(root: tk.Misc) -> None:
    """Idempotently add the resource-monitor button to the active runtime bar."""
    found = _find_health_bar(root)
    if found is None:
        return
    bar, dependency_button = found
    if any(
        isinstance(child, ttk.Button) and str(child.cget("text")) == RESOURCE_BUTTON_TEXT
        for child in bar.winfo_children()
    ):
        return

    button = ttk.Button(
        bar,
        text=RESOURCE_BUTTON_TEXT,
        command=lambda: _show_resource_monitor(root),
    )
    button.pack(side="right", padx=(8, 0), before=dependency_button)
