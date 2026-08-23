from __future__ import annotations

import tkinter as tk
from collections.abc import Callable


def bind_copy_shortcuts(widget: tk.Text) -> None:
    """Make selection copy reliable on Windows, including non-Latin keyboard layouts."""

    def copy_selection(_event: tk.Event | None = None) -> str | None:
        try:
            text = widget.get("sel.first", "sel.last")
        except tk.TclError:
            return None
        widget.clipboard_clear()
        widget.clipboard_append(text)
        widget.update_idletasks()
        return "break"

    def select_all(_event: tk.Event | None = None) -> str:
        widget.tag_add("sel", "1.0", "end-1c")
        widget.mark_set("insert", "1.0")
        widget.see("1.0")
        return "break"

    def control_key(event: tk.Event) -> str | None:
        keysym = str(getattr(event, "keysym", "")).casefold()
        keycode = int(getattr(event, "keycode", 0) or 0)
        # Windows virtual-key codes C=67, A=65. Cyrillic layouts may report с/ф.
        if keysym in {"c", "с"} or keycode == 67:
            return copy_selection(event)
        if keysym in {"a", "ф"} or keycode == 65:
            return select_all(event)
        return None

    widget.configure(exportselection=True, takefocus=True)
    widget.bind("<Control-KeyPress>", control_key, add="+")
    widget.bind("<Control-Insert>", copy_selection, add="+")


def selected_text_copier(widget: tk.Text) -> Callable[[], None]:
    """Return a callback suitable for a Copy selected command/menu."""

    def callback() -> None:
        try:
            text = widget.get("sel.first", "sel.last")
        except tk.TclError:
            return
        widget.clipboard_clear()
        widget.clipboard_append(text)
        widget.update_idletasks()

    return callback
