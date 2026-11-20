from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from database.models import Prioridade, TipoSenha
from database.repositories import EspecialidadeRepository
from domain.numbering_service import NumberingService
from .widgets import ApplicationFrame, MessageArea, create_button


class ReceptionView(ApplicationFrame):
    def __init__(self, master: tk.Misc, connection, **kwargs):
        super().__init__(master, "Recepção - emissão de senha", **kwargs)
        self.connection = connection
        self.numbering = NumberingService(connection)
        self.specialties = EspecialidadeRepository(connection).list(only_active=True)
        self.specialty_by_label = {
            f"{item.codigo} - {item.nome}": item for item in self.specialties
        }
        self.columnconfigure(1, weight=1)
        ttk.Label(self, text="Especialidade").grid(row=1, column=0, sticky="w", pady=4)
        self.specialty_combo = ttk.Combobox(
            self,
            state="readonly",
            values=tuple(self.specialty_by_label),
        )
        self.specialty_combo.grid(row=1, column=1, sticky="ew", pady=4)
        self.specialty_combo.bind("<<ComboboxSelected>>", self.update_state)
        ttk.Label(self, text="Tipo").grid(row=2, column=0, sticky="w", pady=4)
        self.type_combo = ttk.Combobox(self, state="readonly", values=("N", "P"))
        self.type_combo.grid(row=2, column=1, sticky="ew", pady=4)
        self.type_combo.set("N")
        self.type_combo.bind("<<ComboboxSelected>>", self.update_state)
        ttk.Label(self, text="Prioridade").grid(row=3, column=0, sticky="w", pady=4)
        self.priority_combo = ttk.Combobox(
            self,
            state="disabled",
            values=tuple(item.value for item in Prioridade),
        )
        self.priority_combo.grid(row=3, column=1, sticky="ew", pady=4)
        self.message = MessageArea(self)
        self.message.grid(row=4, column=0, columnspan=2, sticky="w", pady=8)
        self.ticket_label = ttk.Label(self, text="-", font=("TkDefaultFont", 30, "bold"))
        self.ticket_label.grid(row=5, column=0, columnspan=2, pady=12)
        create_button(self, "Emitir senha", self.issue_ticket, 6, 0)
        create_button(self, "Limpar", self.clear, 6, 1)
        if self.specialties:
            self.specialty_combo.current(0)

    def update_state(self, event=None) -> None:
        if self.type_combo.get() == TipoSenha.PREFERENCIAL.value:
            self.priority_combo.configure(state="readonly")
            if not self.priority_combo.get():
                self.priority_combo.current(0)
        else:
            self.priority_combo.set("")
            self.priority_combo.configure(state="disabled")

    def issue_ticket(self) -> None:
        specialty = self.specialty_by_label.get(self.specialty_combo.get())
        if specialty is None:
            self.message.show("Selecione uma especialidade.", error=True)
            return
        ticket_type = self.type_combo.get()
        priority = self.priority_combo.get() or None
        try:
            ticket = self.numbering.emitir(
                specialty.id,
                specialty.codigo,
                ticket_type,
                priority,
            )
        except (ValueError, TypeError) as error:
            self.message.show(str(error), error=True)
            return
        self.ticket_label.configure(text=ticket.codigo)
        self.message.show("Senha emitida com sucesso.")

    def clear(self) -> None:
        self.ticket_label.configure(text="-")
        self.message.show("")
        self.type_combo.set("N")
        self.update_state()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Recepção")
    root.geometry("520x380")
    root.mainloop()

