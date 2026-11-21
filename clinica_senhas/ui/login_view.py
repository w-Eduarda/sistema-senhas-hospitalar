from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ui.widgets import MessageArea, create_button


class LoginView(ttk.Frame):
    """Tela de login com cartão arredondado e opção de visualizar senha."""

    def __init__(
        self,
        master: tk.Misc,
        authenticate: Callable[[str, str], Optional[object]],
        on_success: Optional[Callable[[object], None]] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.authenticate_user = authenticate
        self.on_success = on_success
        self._show_password = False

        # Cores para simular vidro claro/translúcido sobre o degradê
        self._card_bg = "#f5faff"
        self._card_border = "#b8d4ee"
        self._outer_bg = "#e8f2fc"

        self.canvas = tk.Canvas(
            self,
            width=430,
            height=300,
            bg=self._outer_bg,
            highlightthickness=0,
            borderwidth=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self._draw_rounded_card(10, 10, 420, 290, radius=22)

        # Container interno posicionado sobre o cartão arredondado
        self.inner = tk.Frame(self.canvas, bg=self._card_bg)
        self.canvas.create_window(215, 150, window=self.inner, width=360)

        tk.Label(
            self.inner,
            text="Acesso ao sistema",
            font=("Segoe UI", 16, "bold"),
            fg="#0f4c81",
            bg=self._card_bg,
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        # Campo Login
        tk.Label(
            self.inner,
            text="Login",
            font=("Segoe UI", 10, "bold"),
            fg="#1e293b",
            bg=self._card_bg,
            anchor="w",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 3))

        self.login_entry = ttk.Entry(self.inner, font=("Segoe UI", 10))
        self.login_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Campo Senha + botão visualizar
        tk.Label(
            self.inner,
            text="Senha",
            font=("Segoe UI", 10, "bold"),
            fg="#1e293b",
            bg=self._card_bg,
            anchor="w",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 3))

        pwd_row = tk.Frame(self.inner, bg=self._card_bg)
        pwd_row.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        pwd_row.columnconfigure(0, weight=1)

        self.password_entry = ttk.Entry(pwd_row, show="*", font=("Segoe UI", 10))
        self.password_entry.grid(row=0, column=0, sticky="ew")

        self.toggle_pwd_btn = ttk.Button(
            pwd_row,
            text="Mostrar",
            width=8,
            command=self.toggle_password,
        )
        self.toggle_pwd_btn.grid(row=0, column=1, padx=(6, 0))

        # Área de mensagens
        self.message = MessageArea(self.inner)
        self.message.configure(background=self._card_bg)
        self.message.grid(row=5, column=0, columnspan=2, sticky="w", pady=(4, 10))

        # Botões Entrar e Limpar
        self.inner.columnconfigure(0, weight=1)
        self.inner.columnconfigure(1, weight=1)
        create_button(self.inner, "Entrar", self.submit, 6, 0, style="Primary.TButton")
        create_button(self.inner, "Limpar", self.clear, 6, 1)

        self.login_entry.bind("<Return>", lambda event: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda event: self.submit())
        self.login_entry.focus_set()

    def _draw_rounded_card(self, x1: int, y1: int, x2: int, y2: int, radius: int = 20) -> None:
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        self.canvas.create_polygon(
            points,
            smooth=True,
            fill=self._card_bg,
            outline=self._card_border,
            width=2,
        )

    def toggle_password(self) -> None:
        self._show_password = not self._show_password
        if self._show_password:
            self.password_entry.configure(show="")
            self.toggle_pwd_btn.configure(text="Ocultar")
        else:
            self.password_entry.configure(show="*")
            self.toggle_pwd_btn.configure(text="Mostrar")

    def submit(self) -> None:
        user = self.authenticate_user(self.login_entry.get(), self.password_entry.get())
        if user is None:
            self.message.show("Login ou senha inválidos.", error=True)
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus_set()
            return
        self.message.show("Login realizado.")
        if self.on_success is not None:
            self.on_success(user)

    def clear(self) -> None:
        self.login_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self._show_password = False
        self.password_entry.configure(show="*")
        self.toggle_pwd_btn.configure(text="Mostrar")
        self.message.show("")
        self.login_entry.focus_set()


if __name__ == "__main__":
    from ui import theme

    root = tk.Tk()
    root.title("Sistema de Senhas - Login")
    root.geometry("480x340")
    theme.init(root)
    LoginView(root, lambda login, senha: None).pack(fill="both", expand=True)
    root.mainloop()