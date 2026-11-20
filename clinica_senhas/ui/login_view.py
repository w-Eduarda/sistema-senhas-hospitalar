from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from database.repositories import UsuarioRepository
from .widgets import ApplicationFrame, MessageArea, create_button, labeled_entry


class LoginView(ApplicationFrame):
    def __init__(
        self,
        master: tk.Misc,
        connection,
        on_success: Optional[Callable[[object], None]] = None,
        **kwargs,
    ):
        super().__init__(master, "Acesso ao sistema", **kwargs)
        self.connection = connection
        self.on_success = on_success
        self.repository = UsuarioRepository(connection)
        self.columnconfigure(1, weight=1)
        self.login_entry = labeled_entry(self, "Login", 1)
        self.password_entry = labeled_entry(self, "Senha", 2, show="*")
        self.message = MessageArea(self)
        self.message.grid(row=3, column=0, columnspan=2, sticky="w", pady=8)
        create_button(self, "Entrar", self.authenticate, 4, 0)
        create_button(self, "Limpar", self.clear, 4, 1)
        self.password_entry.bind("<Return>", lambda event: self.authenticate())
        self.login_entry.focus_set()

    def authenticate(self) -> None:
        login = self.login_entry.get().strip()
        password = self.password_entry.get()
        user = self.repository.get_by_login(login)
        if user is None or not user.ativo or user.senha_hash != password:
            self.message.show("Login ou senha inválidos.", error=True)
            return
        self.message.show("Login realizado.")
        if self.on_success is not None:
            self.on_success(user)

    def clear(self) -> None:
        self.login_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.message.show("")
        self.login_entry.focus_set()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Sistema de Senhas")
    root.geometry("420x230")
    connection = None
    root.mainloop()

