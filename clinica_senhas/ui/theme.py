from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


CORES = {
    "primaria": "#0f4c81",
    "primaria_hover": "#0b3a63",
    "secundaria": "#e6f0fa",
    "destaque": "#1d70b8",
    "fundo": "#eef3f8",
    "superficie": "#ffffff",
    "borda": "#cbd5e1",
    "texto": "#1e293b",
    "muted": "#64748b",
    "erro": "#b91c1c",
    "sucesso": "#15803d",
    "aviso": "#b45309",
    "contraste_fundo": "#000000",
    "contraste_superficie": "#121212",
    "contraste_texto": "#ffffff",
    "contraste_destaque": "#ffd000",
    "contraste_borda": "#ffffff",
}

_HIGH_CONTRAST = False
_FONT_SCALE = 1.0
_SUBSCRIBERS: list[Callable[[], None]] = []


def _font(size: int, weight: str = "normal") -> tuple[str, int] | tuple[str, int, str]:
    scaled = max(8, int(round(size * _FONT_SCALE)))
    return ("Segoe UI", scaled, weight) if weight != "normal" else ("Segoe UI", scaled)


def configurar_tema(root) -> ttk.Style:
    style = ttk.Style(root)
    style.theme_use("clam")

    if _HIGH_CONTRAST:
        bg = CORES["contraste_fundo"]
        surface = CORES["contraste_superficie"]
        fg = CORES["contraste_texto"]
        muted = "#e2e8f0"
        border = CORES["contraste_borda"]
        btn_bg = "#1e1e1e"
        btn_fg = CORES["contraste_destaque"]
        active_bg = CORES["contraste_destaque"]
        active_fg = "#000000"
        primary_bg = CORES["contraste_destaque"]
        primary_fg = "#000000"
        heading_fg = CORES["contraste_destaque"]
        error_fg = "#ff6b6b"
        success_fg = "#4ade80"
        warning_fg = "#facc15"
    else:
        bg = CORES["fundo"]
        surface = CORES["superficie"]
        fg = CORES["texto"]
        muted = CORES["muted"]
        border = CORES["borda"]
        btn_bg = CORES["secundaria"]
        btn_fg = CORES["primaria"]
        active_bg = CORES["destaque"]
        active_fg = "#ffffff"
        primary_bg = CORES["primaria"]
        primary_fg = "#ffffff"
        heading_fg = CORES["primaria"]
        error_fg = CORES["erro"]
        success_fg = CORES["sucesso"]
        warning_fg = CORES["aviso"]

    style.configure(".", background=bg, foreground=fg, font=_font(10))
    style.configure("TFrame", background=bg)
    style.configure("Surface.TFrame", background=surface)
    style.configure(
        "Card.TFrame",
        background=surface,
        relief="solid",
        borderwidth=1,
    )

    style.configure("TLabel", background=bg, foreground=fg, font=_font(10))
    style.configure(
        "Heading.TLabel",
        background=bg,
        foreground=heading_fg,
        font=_font(18, "bold"),
    )
    style.configure(
        "Subheading.TLabel",
        background=bg,
        foreground=fg,
        font=_font(12, "bold"),
    )
    style.configure(
        "Muted.TLabel",
        background=bg,
        foreground=muted,
        font=_font(9),
    )
    style.configure(
        "Error.TLabel",
        background=bg,
        foreground=error_fg,
        font=_font(10, "bold"),
    )
    style.configure(
        "Success.TLabel",
        background=bg,
        foreground=success_fg,
        font=_font(10, "bold"),
    )
    style.configure(
        "Warning.TLabel",
        background=bg,
        foreground=warning_fg,
        font=_font(10, "bold"),
    )

    style.configure(
        "TLabelFrame",
        background=surface,
        foreground=heading_fg,
        bordercolor=border,
        relief="solid",
        borderwidth=1,
    )
    style.configure(
        "TLabelframe.Label",
        background=surface,
        foreground=heading_fg,
        font=_font(10, "bold"),
    )

    style.configure(
        "TButton",
        background=btn_bg,
        foreground=btn_fg,
        bordercolor=border,
        padding=(12, 7),
        font=_font(10, "bold"),
    )
    style.map(
        "TButton",
        background=[
            ("active", active_bg),
            ("pressed", primary_bg),
            ("disabled", bg),
        ],
        foreground=[
            ("active", active_fg),
            ("pressed", primary_fg),
            ("disabled", muted),
        ],
    )

    style.configure(
        "Primary.TButton",
        background=primary_bg,
        foreground=primary_fg,
        bordercolor=primary_bg,
        padding=(14, 7),
        font=_font(10, "bold"),
    )
    style.map(
        "Primary.TButton",
        background=[
            ("active", CORES["primaria_hover"] if not _HIGH_CONTRAST else "#ffe047"),
            ("pressed", primary_bg),
            ("disabled", bg),
        ],
        foreground=[
            ("active", primary_fg),
            ("pressed", primary_fg),
            ("disabled", muted),
        ],
    )

    style.configure(
        "TEntry",
        fieldbackground=surface,
        foreground=fg,
        bordercolor=border,
        padding=(8, 6),
        font=_font(10),
    )
    style.configure(
        "TCombobox",
        fieldbackground=surface,
        foreground=fg,
        bordercolor=border,
        arrowcolor=heading_fg,
        padding=(6, 5),
        font=_font(10),
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", surface)],
        foreground=[("readonly", fg)],
    )

    style.configure("TNotebook", background=bg, bordercolor=border)
    style.configure(
        "TNotebook.Tab",
        background=btn_bg,
        foreground=btn_fg,
        padding=(14, 8),
        font=_font(10, "bold"),
    )
    style.map(
        "TNotebook.Tab",
        background=[
            ("selected", primary_bg),
            ("active", active_bg),
        ],
        foreground=[
            ("selected", primary_fg),
            ("active", active_fg),
        ],
    )

    style.configure(
        "Treeview",
        background=surface,
        foreground=fg,
        fieldbackground=surface,
        bordercolor=border,
        rowheight=max(24, int(round(28 * _FONT_SCALE))),
        font=_font(10),
    )
    style.configure(
        "Treeview.Heading",
        background=btn_bg,
        foreground=heading_fg,
        relief="flat",
        padding=(8, 6),
        font=_font(10, "bold"),
    )
    style.map(
        "Treeview",
        background=[("selected", primary_bg)],
        foreground=[("selected", primary_fg)],
    )

    try:
        top = root.winfo_toplevel()
        if isinstance(top, (tk.Tk, tk.Toplevel)):
            top.configure(background=bg)
    except Exception:
        pass

    return style


def init(root) -> ttk.Style:
    return configurar_tema(root)


def ensure(root) -> ttk.Style:
    return configurar_tema(root)


def is_high_contrast() -> bool:
    return _HIGH_CONTRAST


def set_high_contrast(enabled: bool, root=None) -> bool:
    global _HIGH_CONTRAST
    _HIGH_CONTRAST = bool(enabled)
    if root is not None:
        configurar_tema(root)
    _notify_subscribers()
    return _HIGH_CONTRAST


def toggle_high_contrast(root=None) -> bool:
    return set_high_contrast(not _HIGH_CONTRAST, root=root)


def adjust_font_scale(delta: float, root=None) -> float:
    global _FONT_SCALE
    _FONT_SCALE = max(0.8, min(1.5, round(_FONT_SCALE + delta, 2)))
    if root is not None:
        configurar_tema(root)
    _notify_subscribers()
    return _FONT_SCALE


def decrease_font(root=None) -> float:
    return adjust_font_scale(-0.1, root=root)


def increase_font(root=None) -> float:
    return adjust_font_scale(0.1, root=root)


def priority_key(code: str | None) -> str:
    if not code:
        return "normal"
    normalized = str(code).strip().upper()
    if normalized in {"P1", "P2"}:
        return "alta"
    if normalized in {"P3", "P4"}:
        return "media"
    if normalized in {"P5", "P6"}:
        return "baixa"
    return "normal"


def subscribe(callback: Callable[[], None]) -> None:
    if callback not in _SUBSCRIBERS:
        _SUBSCRIBERS.append(callback)


def _notify_subscribers() -> None:
    for callback in list(_SUBSCRIBERS):
        try:
            callback()
        except Exception:
            pass