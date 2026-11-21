"""Janela principal: cabeçalho, login, navegação por perfil e troca de telas."""
from __future__ import annotations

import importlib
import sys
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import ttk

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from domain.auth_service import AuthService
from ui import theme
from ui.login_view import LoginView

# chave -> (texto do botão, módulo, classe)
SCREENS = {
    "recepcao": ("Recepção", "ui.reception_view", "ReceptionView"),
    "operador": ("Operador", "ui.operator_view", "OperatorView"),
    "painel": ("Painel público", "ui.display_view", "DisplayView"),
    "admin": ("Administração", "ui.admin_view", "AdminView"),
}

# Quais telas cada perfil enxerga (edite aqui para mudar permissões da navegação).
PERFIL_TELAS = {
    "Administrador": ("recepcao", "operador", "painel", "admin"),
    "Recepção": ("recepcao", "painel"),
    "Profissional": ("operador", "painel"),
    "Coordenação": ("recepcao", "operador", "painel"),
}

SCREENS_WITH_CONNECTION = {"recepcao", "operador", "painel", "admin"}


class MainWindow:
    def __init__(self, root: tk.Tk, connection) -> None:
        self.root = root
        self.connection = connection
        self.auth = AuthService(connection)
        self.user = None
        self.nav_buttons: dict[str, ttk.Button] = {}

        theme.init(root)
        root.title("Sistema de Senhas")
        root.geometry("1000x720")
        root.minsize(820, 580)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        self.header = ttk.Frame(root, padding=(16, 10))
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.columnconfigure(1, weight=1)
        ttk.Label(self.header, text="Sistema de Senhas", style="Heading.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.user_label = ttk.Label(self.header, text="", style="Muted.TLabel")
        self.user_label.grid(row=0, column=1, sticky="e", padx=12)

        font_controls = ttk.Frame(self.header)
        font_controls.grid(row=0, column=2)
        ttk.Button(font_controls, text="A-", width=3, command=theme.decrease_font).pack(
            side="left", padx=(0, 4)
        )
        ttk.Button(font_controls, text="A+", width=3, command=theme.increase_font).pack(
            side="left"
        )

        self.logout_button = ttk.Button(self.header, text="Sair", command=self.logout)
        self.logout_button.grid(row=0, column=3, padx=(8, 0))

        self.nav = ttk.Frame(root, padding=(16, 0))
        self.nav.grid(row=1, column=0, sticky="ew")

        self.content = ttk.Frame(root)
        self.content.grid(row=2, column=0, sticky="nsew")

        self._init_gradient_background()
        self.show_login()

    # --- fundo degradê -----------------------------------------------------
    def _init_gradient_background(self) -> None:
        self._bg_canvas = tk.Canvas(
            self.content,
            highlightthickness=0,
            borderwidth=0,
        )
        self._bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._bg_canvas.bind("<Configure>", self._draw_gradient)
        tk.Misc.lower(self._bg_canvas)
        self._draw_gradient()

    @staticmethod
    def _interpolate_hex(start_hex: str, end_hex: str, factor: float) -> str:
        start = tuple(int(start_hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
        end = tuple(int(end_hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
        rgb = tuple(int(start[i] + (end[i] - start[i]) * factor) for i in range(3))
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def _draw_gradient(self, event=None) -> None:
        if not hasattr(self, "_bg_canvas") or not self._bg_canvas.winfo_exists():
            return
        width = max(self._bg_canvas.winfo_width(), 1)
        height = max(self._bg_canvas.winfo_height(), 1)
        self._bg_canvas.delete("gradient")

        top_color = "#ffffff"
        bottom_color = "#4fa5f1"
        steps = min(height, 120)
        for i in range(steps):
            y0 = int((i / steps) * height)
            y1 = int(((i + 1) / steps) * height) + 1
            color = self._interpolate_hex(top_color, bottom_color, i / max(steps - 1, 1))
            self._bg_canvas.create_rectangle(
                0,
                y0,
                width,
                y1,
                outline="",
                fill=color,
                tags="gradient",
            )
        tk.Misc.lower(self._bg_canvas)

    # --- login / logout ----------------------------------------------------
    def show_login(self) -> None:
        self.user = None
        self._clear(self.nav)
        self._clear(self.content)
        self._init_gradient_background()
        self.nav.grid_remove()
        self.logout_button.grid_remove()
        self.user_label.configure(text="")
        holder = ttk.Frame(self.content)
        holder.place(relx=0.5, rely=0.45, anchor="center")
        LoginView(holder, self.auth.authenticate, on_success=self.on_login).pack()
        tk.Misc.lower(self._bg_canvas)

    def on_login(self, user) -> None:
        self.user = user
        self.user_label.configure(text=f"{user.login} ({user.perfil.value})")
        self.logout_button.grid()
        self.nav.grid()
        self._build_nav()
        self.navigate(PERFIL_TELAS[user.perfil.value][0])

    def logout(self) -> None:
        self.show_login()

    # --- navegação -----------------------------------------------------------
    def _build_nav(self) -> None:
        self._clear(self.nav)
        self.nav_buttons = {}
        for key in PERFIL_TELAS[self.user.perfil.value]:
            button = ttk.Button(
                self.nav, text=SCREENS[key][0], command=lambda k=key: self.navigate(k)
            )
            button.pack(side="left", padx=(0, 6), pady=(0, 8))
            self.nav_buttons[key] = button

    def navigate(self, key: str) -> None:
        for name, button in self.nav_buttons.items():
            button.configure(style="Primary.TButton" if name == key else "TButton")
        self._clear(self.content)
        self._init_gradient_background()
        try:
            _, module_name, class_name = SCREENS[key]
            view_class = getattr(importlib.import_module(module_name), class_name)
            if key in SCREENS_WITH_CONNECTION:
                # TODO operador: passar professional_id do profissional logado
                view = view_class(self.content, self.connection)
            else:
                view = view_class(self.content)
            view.pack(fill="both", expand=True)
        except Exception as error:  # uma tela quebrada não derruba as outras
            traceback.print_exc()
            frame = ttk.Frame(self.content, padding=24)
            frame.pack(fill="both", expand=True)
            ttk.Label(
                frame, text="Não foi possível abrir esta tela.", style="Error.TLabel"
            ).pack(anchor="w")
            ttk.Label(frame, text=str(error), wraplength=700).pack(anchor="w", pady=8)
        tk.Misc.lower(self._bg_canvas)

    @staticmethod
    def _clear(frame: ttk.Frame) -> None:
        for child in frame.winfo_children():
            child.destroy()