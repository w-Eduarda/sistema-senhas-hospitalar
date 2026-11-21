from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database.repositories import EspecialidadeRepository, ProfissionalRepository
from domain.queue_service import QueueService
from .widgets import MessageArea, PasswordCard, create_button


class OperatorView(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        connection,
        professional_id: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(master, padding=24, **kwargs)
        self.connection = connection
        self.queue = QueueService(connection)
        self.specialties = EspecialidadeRepository(connection).list(only_active=True)

        self.professional_id = professional_id
        self.current_password = None
        self.current_attendance = None
        self.turn_count = 0

        self.columnconfigure(0, weight=1)

        card = ttk.Frame(self, padding=24, style="Card.TFrame")
        card.grid(row=0, column=0, sticky="ew")
        card.columnconfigure(1, weight=1)

        ttk.Label(
            card,
            text="Painel do Profissional",
            style="Heading.TLabel",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        self.prof_label = ttk.Label(
            card,
            text="Profissional ativo: —",
            style="Muted.TLabel",
        )
        self.prof_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 2))

        self.turn_label = ttk.Label(
            card,
            text="Atendimentos no turno: 0",
            style="Muted.TLabel",
        )
        self.turn_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(card, text="Especialidade", style="Subheading.TLabel").grid(
            row=3, column=0, sticky="w", padx=(0, 14), pady=6
        )
        self.specialty_combo = ttk.Combobox(
            card,
            state="readonly",
            values=tuple(f"{item.id} - {item.codigo}" for item in self.specialties),
        )
        self.specialty_combo.grid(row=3, column=1, sticky="ew", pady=6)
        self.specialty_combo.bind("<<ComboboxSelected>>", self._on_specialty_change)

        self.card = PasswordCard(card)
        self.card.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 4))

        self.detail_label = ttk.Label(
            card,
            text="",
            style="Muted.TLabel",
        )
        self.detail_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.message = MessageArea(card)
        self.message.grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 10))

        buttons = ttk.Frame(card, style="Surface.TFrame")
        buttons.grid(row=7, column=0, columnspan=2, sticky="ew")
        for column in range(3):
            buttons.columnconfigure(column, weight=1)

        create_button(
            buttons,
            "Chamar próxima",
            self.call_next,
            0,
            0,
            style="Primary.TButton",
        )
        create_button(buttons, "Rechamar", self.recall, 0, 1)
        create_button(buttons, "Iniciar", self.start, 0, 2)
        create_button(buttons, "Finalizar", self.finish, 1, 0)
        create_button(buttons, "Ausente", self.absent, 1, 1)
        create_button(buttons, "Cancelar", self.cancel, 1, 2)

        if self.specialties:
            self.specialty_combo.current(0)
            self._on_specialty_change()

    def specialty_id(self) -> Optional[int]:
        value = self.specialty_combo.get().split(" - ", 1)[0]
        return int(value) if value.isdigit() else None

    def _format_professional_info(self, prof_id: int) -> str:
        try:
            pros = ProfissionalRepository(self.connection).list(only_active=False)
            for p in pros:
                if getattr(p, "id", None) == prof_id:
                    nome = getattr(p, "nome", f"#{prof_id}")
                    cons_id = getattr(p, "consultorio_id", None)
                    if cons_id is not None:
                        return f"Profissional ativo: {nome} (#{prof_id}) • Consultório #{cons_id}"
                    return f"Profissional ativo: {nome} (#{prof_id})"
        except Exception:
            pass
        return f"Profissional ativo: #{prof_id}"

    def _on_specialty_change(self, event=None) -> None:
        spec_id = self.specialty_id()
        if spec_id is not None:
            resolved = self._ensure_professional_for_specialty(spec_id)
            if resolved is not None:
                self.professional_id = resolved
                self.prof_label.configure(text=self._format_professional_info(self.professional_id))

    def _ensure_professional_for_specialty(self, specialty_id: int) -> Optional[int]:
        try:
            pros = ProfissionalRepository(self.connection).list(only_active=True)
            matching = [
                p for p in pros if getattr(p, "especialidade_id", None) == specialty_id
            ]
            if matching:
                return matching[0].id
        except Exception:
            pass

        try:
            cur = self.connection.cursor()
            cur.execute(
                """
                INSERT INTO profissionais (nome, registro, especialidade_id, ativo)
                VALUES (?, ?, ?, 1)
                """,
                (f"Profissional {specialty_id}", f"REG-{specialty_id:03d}", specialty_id),
            )
            self.connection.commit()
            return cur.lastrowid
        except Exception:
            return self.professional_id

    def call_next(self) -> None:
        specialty_id = self.specialty_id()
        if specialty_id is None:
            self.message.show("Selecione uma especialidade.", error=True)
            return

        self.current_password = self.queue.chamar_proxima(specialty_id)
        if self.current_password is None:
            self.message.show("Não há senhas aguardando.", error=True)
            self.card.show("-", "")
            self.detail_label.configure(text="")
            return

        self.card.show(self.current_password.codigo, self.current_password.status.value)
        prio = getattr(self.current_password, "prioridade", None)
        tipo = getattr(self.current_password, "tipo", "")
        info_partes = []
        if tipo:
            info_partes.append(f"Tipo: {tipo}")
        if prio:
            info_partes.append(f"Prioridade: {prio}")
        self.detail_label.configure(text=" • ".join(info_partes))
        self.message.show("Senha chamada.")

    def recall(self) -> None:
        if self.current_password is None:
            self.message.show("Nenhuma senha chamada para rechamar.", error=True)
            return
        try:
            if hasattr(self.queue, "rechamar"):
                self.queue.rechamar(self.current_password.id)
            elif hasattr(self.queue, "rechamar_senha"):
                self.queue.rechamar_senha(self.current_password.id)
            self.card.show(self.current_password.codigo, self.current_password.status.value)
            self.message.show("Senha rechamada.")
        except ValueError as error:
            self.message.show(str(error), error=True)

    def start(self) -> None:
        if self.current_password is None:
            self.message.show("Chame uma senha antes de iniciar.", error=True)
            return

        specialty_id = self.specialty_id()
        prof_id = (
            self._ensure_professional_for_specialty(specialty_id)
            if specialty_id is not None
            else self.professional_id
        )
        if prof_id is None:
            self.message.show("Informe o profissional para iniciar.", error=True)
            return

        try:
            self.current_attendance = self.queue.iniciar_atendimento(
                self.current_password.id,
                prof_id,
            )
            self.professional_id = prof_id
            self.prof_label.configure(text=self._format_professional_info(self.professional_id))
            self.card.show(self.current_password.codigo, "Em atendimento")
            self.message.show("Atendimento iniciado.")
        except ValueError as error:
            self.message.show(str(error), error=True)

    def finish(self) -> None:
        if self.current_attendance is None:
            self.message.show("Não há atendimento em andamento.", error=True)
            return

        try:
            self.queue.finalizar_atendimento(self.current_attendance.id, "Concluído")
            self.turn_count += 1
            self.turn_label.configure(text=f"Atendimentos no turno: {self.turn_count}")
            self.card.show("-", "Finalizado")
            self.detail_label.configure(text="")
            self.message.show("Atendimento finalizado.")
            self.current_attendance = None
            self.current_password = None
        except ValueError as error:
            self.message.show(str(error), error=True)

    def absent(self) -> None:
        if self.current_password is None:
            return
        try:
            self.queue.marcar_ausente(self.current_password.id)
            self.card.show("-", "Ausente")
            self.detail_label.configure(text="")
            self.message.show("Paciente marcado como ausente.")
            self.current_attendance = None
            self.current_password = None
        except ValueError as error:
            self.message.show(str(error), error=True)

    def cancel(self) -> None:
        if self.current_password is None:
            return
        try:
            self.queue.cancelar(self.current_password.id)
            self.card.show("-", "Cancelada")
            self.detail_label.configure(text="")
            self.message.show("Senha cancelada.")
            self.current_attendance = None
            self.current_password = None
        except ValueError as error:
            self.message.show(str(error), error=True)


if __name__ == "__main__":
    from database.connection import Database
    from ui import theme

    root = tk.Tk()
    root.title("Painel do profissional")
    root.geometry("680x520")
    theme.init(root)
    with Database(":memory:") as database:
        view = OperatorView(root, database.connection, professional_id=1)
        view.pack(fill="both", expand=True)
        root.mainloop()