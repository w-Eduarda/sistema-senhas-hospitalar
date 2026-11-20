from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from typing import Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from .widgets import ApplicationFrame, PasswordCard
except ImportError:
    from ui.widgets import ApplicationFrame, PasswordCard


class DisplayView(ApplicationFrame):
    def __init__(self, master: tk.Misc, **kwargs):
        super().__init__(master, "Painel de chamadas", **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.card = PasswordCard(self)
        self.card.grid(row=1, column=0, sticky="nsew", pady=16)

        self.history = tk.Listbox(self, height=8, font=("TkDefaultFont", 14))
        self.history.grid(row=2, column=0, sticky="nsew")

    def show_call(self, code: str, office: Optional[str] = None) -> None:
        details = f"Consultório {office}" if office else ""
        self.card.show(code, details)

        entry = f"{code} - {details}" if details else code
        self.history.insert(0, entry)
        if self.history.size() > 8:
            self.history.delete(8, tk.END)

    def clear_history(self) -> None:
        self.history.delete(0, tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Painel público")
    root.geometry("700x560")
    view = DisplayView(root)
    view.pack(fill="both", expand=True)
    view.show_call("CG-P-001", "01")
    root.mainloop()
