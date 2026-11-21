"""Ponto de entrada do Sistema de Senhas.

Rode SEMPRE a partir da raiz (a pasta clinica_senhas):

    python app.py
"""
from __future__ import annotations

import tkinter as tk

from config import DATABASE_PATH
from database.connection import Database
from domain.auth_service import AuthService
from ui.main_window import MainWindow


def main() -> None:
    with Database(DATABASE_PATH) as database:
        criados = AuthService(database.connection).ensure_default_users()
        if criados:
            print("Usuários de desenvolvimento criados (senha: senha123):")
            print(", ".join(criados))
        root = tk.Tk()
        MainWindow(root, database.connection)
        root.mainloop()


if __name__ == "__main__":
    main()
