from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database.repositories import (
    ConsultorioRepository,
    EspecialidadeRepository,
    ProfissionalRepository,
)
from .widgets import ApplicationFrame, DataTable, MessageArea


class AdminView(ApplicationFrame):
    def __init__(self, master: tk.Misc, connection, **kwargs):
        super().__init__(master, "Painel administrativo", **kwargs)
        self.connection = connection
        self.specialties = EspecialidadeRepository(connection)
        self.offices = ConsultorioRepository(connection)
        self.professionals = ProfissionalRepository(connection)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        self.specialty_table = DataTable(self.notebook, ("id", "codigo", "nome", "ativo"))
        self.office_table = DataTable(self.notebook, ("id", "numero", "descricao", "ativo"))
        self.professional_table = DataTable(
            self.notebook, ("id", "nome", "registro", "especialidade", "ativo")
        )

        self.notebook.add(self.specialty_table, text="Especialidades")
        self.notebook.add(self.office_table, text="Consultórios")
        self.notebook.add(self.professional_table, text="Profissionais")

        self.message = MessageArea(self)
        self.message.grid(row=2, column=0, sticky="w", pady=8)

        ttk.Button(self, text="Atualizar", command=self.refresh).grid(
            row=3, column=0, sticky="e"
        )
        self.refresh()

    def _format_bool(self, value: bool) -> str:
        return "Sim" if value else "Não"

    def refresh(self) -> None:
        try:
            self.specialty_table.clear()
            for item in self.specialties.list():
                self.specialty_table.add_row(
                    (item.id, item.codigo, item.nome, self._format_bool(bool(item.ativo)))
                )

            self.office_table.clear()
            for item in self.offices.list():
                self.office_table.add_row(
                    (
                        item.id,
                        item.numero,
                        item.descricao or "",
                        self._format_bool(bool(item.ativo)),
                    )
                )

            self.professional_table.clear()
            for item in self.professionals.list():
                self.professional_table.add_row(
                    (
                        item.id,
                        item.nome,
                        item.registro,
                        item.especialidade_id,
                        self._format_bool(bool(item.ativo)),
                    )
                )

            self.message.show("Dados atualizados.")
        except Exception as exc:
            self.message.show(f"Erro ao atualizar dados: {exc}")


if __name__ == "__main__":
    from database.connection import Database

    root = tk.Tk()
    root.title("Administração")
    root.geometry("820x520")
    with Database(":memory:") as database:
        view = AdminView(root, database.connection)
        view.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        root.mainloop()
