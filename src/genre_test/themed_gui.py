from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk
from typing import Final

from .logging_utils import append_log

DARK_LABEL: Final = "Тёмная"
LIGHT_LABEL: Final = "Светлая"
THEME_LABELS: Final = (DARK_LABEL, LIGHT_LABEL)
DEFAULT_THEME: Final = DARK_LABEL


@dataclass(frozen=True)
class Palette:
    window: str
    panel: str
    field: str
    text: str
    muted: str
    border: str
    select: str
    selected_text: str
    link: str


PALETTES: Final[dict[str, Palette]] = {
    DARK_LABEL: Palette(
        window="#17191d",
        panel="#202329",
        field="#111317",
        text="#e7e9ed",
        muted="#aeb4bf",
        border="#454b55",
        select="#365f91",
        selected_text="#ffffff",
        link="#72a7ff",
    ),
    LIGHT_LABEL: Palette(
        window="#f3f3f3",
        panel="#f7f7f7",
        field="#ffffff",
        text="#171717",
        muted="#555555",
        border="#b9b9b9",
        select="#0a64ad",
        selected_text="#ffffff",
        link="#0563c1",
    ),
}


def normalize_theme_label(value: str) -> str:
    return value if value in PALETTES else DEFAULT_THEME


def _configure_ttk(root: tk.Misc, palette: Palette) -> None:
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    style.configure(".", background=palette.panel, foreground=palette.text)
    style.configure("TFrame", background=palette.panel)
    style.configure("TLabel", background=palette.panel, foreground=palette.text)
    style.configure("TLabelframe", background=palette.panel, foreground=palette.text)
    style.configure("TLabelframe.Label", background=palette.panel, foreground=palette.text)
    style.configure(
        "TButton",
        background=palette.panel,
        foreground=palette.text,
        bordercolor=palette.border,
        lightcolor=palette.border,
        darkcolor=palette.border,
    )
    style.map(
        "TButton",
        background=[("active", palette.select), ("pressed", palette.select)],
        foreground=[("active", palette.selected_text), ("pressed", palette.selected_text)],
    )
    style.configure("TCheckbutton", background=palette.panel, foreground=palette.text)
    style.configure("TRadiobutton", background=palette.panel, foreground=palette.text)
    style.map(
        "TCheckbutton",
        background=[("active", palette.panel)],
        foreground=[("active", palette.text)],
    )
    style.configure(
        "TEntry",
        fieldbackground=palette.field,
        foreground=palette.text,
        insertcolor=palette.text,
        bordercolor=palette.border,
    )
    style.configure(
        "TCombobox",
        fieldbackground=palette.field,
        background=palette.panel,
        foreground=palette.text,
        arrowcolor=palette.text,
        bordercolor=palette.border,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", palette.field)],
        foreground=[("readonly", palette.text)],
        selectbackground=[("readonly", palette.select)],
        selectforeground=[("readonly", palette.selected_text)],
    )
    style.configure(
        "TSpinbox",
        fieldbackground=palette.field,
        background=palette.panel,
        foreground=palette.text,
        arrowcolor=palette.text,
        bordercolor=palette.border,
    )
    style.configure("TNotebook", background=palette.window, bordercolor=palette.border)
    style.configure(
        "TNotebook.Tab",
        background=palette.panel,
        foreground=palette.text,
        padding=(10, 5),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", palette.select), ("active", palette.border)],
        foreground=[("selected", palette.selected_text), ("active", palette.text)],
    )
    style.configure(
        "Treeview",
        background=palette.field,
        fieldbackground=palette.field,
        foreground=palette.text,
        bordercolor=palette.border,
    )
    style.map(
        "Treeview",
        background=[("selected", palette.select)],
        foreground=[("selected", palette.selected_text)],
    )
    style.configure(
        "Treeview.Heading",
        background=palette.panel,
        foreground=palette.text,
        bordercolor=palette.border,
    )
    style.configure("TSeparator", background=palette.border)
    style.configure(
        "Horizontal.TProgressbar",
        background=palette.select,
        troughcolor=palette.field,
        bordercolor=palette.border,
    )
    style.configure(
        "HistoryLink.TLabel",
        background=palette.panel,
        foreground=palette.link,
        font=("Segoe UI", 9, "underline"),
    )

    root.option_add("*TCombobox*Listbox.background", palette.field)
    root.option_add("*TCombobox*Listbox.foreground", palette.text)
    root.option_add("*TCombobox*Listbox.selectBackground", palette.select)
    root.option_add("*TCombobox*Listbox.selectForeground", palette.selected_text)


def _is_link_label(widget: tk.Misc) -> bool:
    try:
        return isinstance(widget, tk.Label) and str(widget.cget("cursor")) == "hand2"
    except tk.TclError:
        return False


def _theme_classic_widget(widget: tk.Misc, palette: Palette) -> None:
    try:
        if isinstance(widget, (tk.Tk, tk.Toplevel)):
            widget.configure(background=palette.window)
        elif isinstance(widget, tk.Text):
            widget.configure(
                background=palette.field,
                foreground=palette.text,
                insertbackground=palette.text,
                selectbackground=palette.select,
                selectforeground=palette.selected_text,
                highlightbackground=palette.border,
                highlightcolor=palette.select,
            )
        elif isinstance(widget, tk.Listbox):
            widget.configure(
                background=palette.field,
                foreground=palette.text,
                selectbackground=palette.select,
                selectforeground=palette.selected_text,
                highlightbackground=palette.border,
            )
        elif isinstance(widget, tk.Entry):
            widget.configure(
                background=palette.field,
                foreground=palette.text,
                insertbackground=palette.text,
                selectbackground=palette.select,
                selectforeground=palette.selected_text,
            )
        elif isinstance(widget, tk.Label):
            foreground = palette.link if _is_link_label(widget) else None
            config: dict[str, str] = {"background": palette.panel}
            current_fg = str(widget.cget("foreground"))
            if foreground is not None:
                config["foreground"] = foreground
            elif current_fg.lower() in {
                "systembuttontext",
                "black",
                "#000000",
                "#000",
            }:
                config["foreground"] = palette.text
            widget.configure(**config)
        elif isinstance(widget, tk.Canvas):
            widget.configure(background=palette.panel, highlightbackground=palette.border)
    except tk.TclError:
        return


def apply_theme(root: tk.Misc, theme_label: str, *, recursive: bool = True) -> None:
    label = normalize_theme_label(theme_label)
    palette = PALETTES[label]
    _configure_ttk(root, palette)
    _theme_classic_widget(root, palette)
    if not recursive:
        return

    stack: list[tk.Misc] = [root]
    while stack:
        parent = stack.pop()
        try:
            children = parent.winfo_children()
        except tk.TclError:
            continue
        for child in children:
            _theme_classic_widget(child, palette)
            stack.append(child)


def _find_health_bar(root: tk.Misc) -> ttk.Frame | None:
    for child in root.winfo_children():
        if not isinstance(child, ttk.Frame):
            continue
        for nested in child.winfo_children():
            if isinstance(nested, ttk.Button) and str(nested.cget("text")) == "Зависимости…":
                return child
    return None


class ThemeController:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.theme_var = tk.StringVar(root, value=DEFAULT_THEME)
        self._installed = False
        self._map_after_id: str | None = None

    def install(self) -> None:
        if self._installed:
            return
        self._installed = True
        self._install_switch()
        self.apply(DEFAULT_THEME, log_change=False)
        self.root.bind_all("<Map>", self._on_map, add="+")

    def _install_switch(self) -> None:
        bar = _find_health_bar(self.root)
        if bar is None:
            return
        ttk.Combobox(
            bar,
            textvariable=self.theme_var,
            values=THEME_LABELS,
            state="readonly",
            width=9,
        ).pack(side="right", padx=(5, 0))
        ttk.Label(bar, text="Тема:").pack(side="right", padx=(10, 0))
        combo = next(
            (
                child
                for child in bar.winfo_children()
                if isinstance(child, ttk.Combobox)
                and str(child.cget("textvariable")) == str(self.theme_var)
            ),
            None,
        )
        if combo is not None:
            combo.bind("<<ComboboxSelected>>", self._on_selected)

    def _on_selected(self, _event=None) -> None:
        self.apply(self.theme_var.get())

    def _on_map(self, _event=None) -> None:
        if self._map_after_id is not None:
            return
        self._map_after_id = self.root.after_idle(self._apply_current_after_map)

    def _apply_current_after_map(self) -> None:
        self._map_after_id = None
        apply_theme(self.root, self.theme_var.get())

    def apply(self, theme_label: str, *, log_change: bool = True) -> None:
        label = normalize_theme_label(theme_label)
        self.theme_var.set(label)
        apply_theme(self.root, label)
        if log_change:
            append_log(f"GUI theme changed: {label}")


def main() -> None:
    from . import runtime_health_gui

    original_tk_init = tk.Tk.__init__
    original_mainloop = tk.Misc.mainloop

    def themed_tk_init(self, *args, **kwargs):
        original_tk_init(self, *args, **kwargs)
        apply_theme(self, DEFAULT_THEME, recursive=False)

    def themed_mainloop(self, n: int = 0):
        root = self._root()
        if isinstance(root, tk.Tk) and not hasattr(root, "_genre_test_theme_controller"):
            controller = ThemeController(root)
            setattr(root, "_genre_test_theme_controller", controller)
            controller.install()
        return original_mainloop(self, n)

    tk.Tk.__init__ = themed_tk_init
    tk.Misc.mainloop = themed_mainloop
    try:
        runtime_health_gui.main()
    finally:
        tk.Tk.__init__ = original_tk_init
        tk.Misc.mainloop = original_mainloop


if __name__ == "__main__":
    main()
