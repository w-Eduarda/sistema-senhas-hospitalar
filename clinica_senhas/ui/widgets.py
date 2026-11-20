
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class ApplicationFrame(ttk.Frame):
    def __init__(self, master: tk.Misc, title: str, **kwargs):
        super().__init__(master, padding=16, **kwargs)
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text=title, font=("TkDefaultFont", 18, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 16)
        )


class MessageArea(ttk.Label):
    def __init__(self, master: tk.Misc, **kwargs):
        super().__init__(master, foreground="#174a7e", **kwargs)

    def show(self, message: str, error: bool = False) -> None:
        self.configure(text=message, foreground="#a00000" if error else "#174a7e")


class PasswordCard(ttk.LabelFrame):
    def __init__(self, master: tk.Misc, **kwargs):
        super().__init__(master, text="Senha chamada", padding=16, **kwargs)
        self.code_label = ttk.Label(self, text="-", font=("TkDefaultFont", 32, "bold"))
        self.code_label.pack(pady=8)
        self.details_label = ttk.Label(self, text="")
        self.details_label.pack()

    def show(self, code: str, details: str = "") -> None:
        self.code_label.configure(text=code)
        self.details_label.configure(text=details)


class DataTable(ttk.Treeview):
    def __init__(self, master: tk.Misc, columns: tuple[str, ...], **kwargs):
        super().__init__(master, columns=columns, show="headings", **kwargs)
        for column in columns:
            self.heading(column, text=column.replace("_", " ").title())
            self.column(column, width=130, anchor="center")

    def clear(self) -> None:
        for item in self.get_children():
            self.delete(item)

    def add_row(self, values: tuple[object, ...]) -> None:
        self.insert("", "end", values=values)


def create_button(
    master: tk.Misc,
    text: str,
    command: Callable[[], None],
    row: int,
    column: int = 0,
    **kwargs,
) -> ttk.Button:
    button = ttk.Button(master, text=text, command=command, **kwargs)
    button.grid(row=row, column=column, padx=4, pady=4, sticky="ew")
    return button


def labeled_entry(
    master: tk.Misc,
    label: str,
    row: int,
    show: Optional[str] = None,
) -> ttk.Entry:
    ttk.Label(master, text=label).grid(row=row, column=0, sticky="w", pady=4)
    entry = ttk.Entry(master, show=show)
    entry.grid(row=row, column=1, sticky="ew", pady=4)
    return entry
