from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from database.repositories import ConfiguracaoRepository, ConsultorioRepository, EspecialidadeRepository, ProfissionalRepository
from .widgets import ApplicationFrame, DataTable, MessageArea


class AdminView(ApplicationFrame):
    def __init__(self, master: tk.Misc, connection, **kwargs):
        super().__init__(master, "Painel administrativo", **kwargs)
        self.connection = connection
        self.specialties = EspecialidadeRepository(connection)
        self.offices = ConsultorioRepository(connection)
        self.professionals = ProfissionalRepository(connection)
        self.settings = ConfiguracaoRepository(connection)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew")
        self.specialty_table = DataTable(self.notebook, ("id", "codigo", "nome", "ativo"))
        self.office_table = DataTable(self.notebook, ("id", "numero", "descricao", "ativo"))
        self.professional_table = DataTable(self.notebook, ("id", "nome", "registro", "especialidade", "ativo"))
        self.notebook.add(self.specialty_table, text="Especialidades")
        self.notebook.add(self.office_table, text="Consultórios")
        self.notebook.add(self.professional_table, text="Profissionais")
        self.message = MessageArea(self)
        self.message.grid(row=2, column=0, sticky="w", pady=8)
        ttk.Button(self, text="Atualizar", command=self.refresh).grid(row=3, column=0, sticky="e")
        self.refresh()

    def refresh(self) -> None:
        self.specialty_table.clear()
        for item in self.specialties.list():
            self.specialty_table.add_row((item.id, item.codigo, item.nome, "Sim" if item.ativo else "Não"))
        self.office_table.clear()
        for item in self.offices.list():
            self.office_table.add_row((item.id, item.numero, item.descricao or "", "Sim" if item.ativo else "Não"))
        self.professional_table.clear()
        for item in self.professionals.list():
            self.professional_table.add_row((item.id, item.nome, item.registro, item.especialidade_id, "Sim" if item.ativo else "Não"))
        self.message.show("Dados atualizados.")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Administração")
    root.geometry("820x520")
    root.mainloop()

