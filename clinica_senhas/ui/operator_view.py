from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from database.repositories import EspecialidadeRepository, ProfissionalRepository
from domain.queue_service import QueueService
from .widgets import ApplicationFrame, MessageArea, PasswordCard, create_button


class OperatorView(ApplicationFrame):
    def __init__(self, master: tk.Misc, connection, professional_id: Optional[int] = None, **kwargs):
        super().__init__(master, "Painel do profissional", **kwargs)
        self.connection = connection
        self.queue = QueueService(connection)
        self.professionals = ProfissionalRepository(connection)
        self.specialties = EspecialidadeRepository(connection).list(only_active=True)
        self.professional_id = professional_id
        self.current_password = None
        self.current_attendance = None
        self.columnconfigure(1, weight=1)
        ttk.Label(self, text="Especialidade").grid(row=1, column=0, sticky="w", pady=4)
        self.specialty_combo = ttk.Combobox(
            self,
            state="readonly",
            values=tuple(f"{item.id} - {item.codigo}" for item in self.specialties),
        )
        self.specialty_combo.grid(row=1, column=1, sticky="ew", pady=4)
        self.card = PasswordCard(self)
        self.card.grid(row=2, column=0, columnspan=2, sticky="ew", pady=12)
        self.message = MessageArea(self)
        self.message.grid(row=3, column=0, columnspan=2, sticky="w", pady=8)
        buttons = ttk.Frame(self)
        buttons.grid(row=4, column=0, columnspan=2, sticky="ew")
        for column in range(3):
            buttons.columnconfigure(column, weight=1)
        create_button(buttons, "Chamar próxima", self.call_next, 0, 0)
        create_button(buttons, "Iniciar", self.start, 0, 1)
        create_button(buttons, "Finalizar", self.finish, 0, 2)
        create_button(buttons, "Ausente", self.absent, 1, 0)
        create_button(buttons, "Cancelar", self.cancel, 1, 1)
        if self.specialties:
            self.specialty_combo.current(0)

    def specialty_id(self) -> Optional[int]:
        value = self.specialty_combo.get().split(" - ", 1)[0]
        return int(value) if value.isdigit() else None

    def call_next(self) -> None:
        specialty_id = self.specialty_id()
        if specialty_id is None:
            self.message.show("Selecione uma especialidade.", error=True)
            return
        self.current_password = self.queue.chamar_proxima(specialty_id)
        if self.current_password is None:
            self.message.show("Não há senhas aguardando.", error=True)
            self.card.show("-", "")
            return
        self.card.show(self.current_password.codigo, self.current_password.status.value)
        self.message.show("Senha chamada.")

    def start(self) -> None:
        if self.current_password is None:
            self.message.show("Chame uma senha antes de iniciar.", error=True)
            return
        if self.professional_id is None:
            self.message.show("Informe o profissional para iniciar.", error=True)
            return
        try:
            self.current_attendance = self.queue.iniciar_atendimento(
                self.current_password.id,
                self.professional_id,
            )
            self.message.show("Atendimento iniciado.")
        except ValueError as error:
            self.message.show(str(error), error=True)

    def finish(self) -> None:
        if self.current_attendance is None:
            self.message.show("Não há atendimento em andamento.", error=True)
            return
        try:
            self.queue.finalizar_atendimento(self.current_attendance.id, "Concluído")
            self.message.show("Atendimento finalizado.")
            self.current_attendance = None
        except ValueError as error:
            self.message.show(str(error), error=True)

    def absent(self) -> None:
        if self.current_password is None:
            return
        try:
            self.queue.marcar_ausente(self.current_password.id)
            self.message.show("Paciente marcado como ausente.")
        except ValueError as error:
            self.message.show(str(error), error=True)

    def cancel(self) -> None:
        if self.current_password is None:
            return
        try:
            self.queue.cancelar(self.current_password.id)
            self.message.show("Senha cancelada.")
        except ValueError as error:
            self.message.show(str(error), error=True)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Painel do profissional")
    root.geometry("620x480")
    root.mainloop()

