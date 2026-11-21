from __future__ import annotations

import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk
from typing import Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database.models import Prioridade, TipoSenha
from database.repositories import EspecialidadeRepository
from domain.numbering_service import NumberingService
from domain.priority_service import PriorityService
from .widgets import MessageArea, create_button

TIPO_OPCOES = {
    "Normal (N)": TipoSenha.NORMAL.value,
    "Preferencial (P)": TipoSenha.PREFERENCIAL.value,
}


class ReceptionView(ttk.Frame):
    def __init__(self, master: tk.Misc, connection, **kwargs):
        super().__init__(master, padding=24, **kwargs)
        self.connection = connection
        self.numbering = NumberingService(connection)
        self.specialties = EspecialidadeRepository(connection).list(only_active=True)

        self.specialty_by_label = {
            f"{item.codigo} — {item.nome}": item for item in self.specialties
        }
        self.priority_by_label = {
            f"{code.value} — {desc}": code.value
            for code, desc in PriorityService.CATEGORIAS.items()
        }

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Cartão centralizado com borda suave
        card = ttk.Frame(self, padding=28, style="Card.TFrame")
        card.grid(row=0, column=0, sticky="n", pady=(8, 0))
        card.columnconfigure(1, weight=1)

        ttk.Label(
            card,
            text="Recepção — Emissão de Senha",
            style="Heading.TLabel",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        ttk.Label(
            card,
            text="Selecione a especialidade, o tipo de atendimento e a prioridade (quando aplicável).",
            style="Muted.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 14))

        # Especialidade
        ttk.Label(card, text="Especialidade", style="Subheading.TLabel").grid(
            row=2, column=0, sticky="w", padx=(0, 16), pady=6
        )
        self.specialty_combo = ttk.Combobox(
            card,
            state="readonly",
            width=38,
            values=tuple(self.specialty_by_label),
        )
        self.specialty_combo.grid(row=2, column=1, sticky="ew", pady=6)
        self.specialty_combo.bind("<<ComboboxSelected>>", self.update_state)

        # Tipo
        ttk.Label(card, text="Tipo de senha", style="Subheading.TLabel").grid(
            row=3, column=0, sticky="w", padx=(0, 16), pady=6
        )
        self.type_combo = ttk.Combobox(
            card,
            state="readonly",
            width=38,
            values=tuple(TIPO_OPCOES),
        )
        self.type_combo.grid(row=3, column=1, sticky="ew", pady=6)
        self.type_combo.set("Normal (N)")
        self.type_combo.bind("<<ComboboxSelected>>", self.update_state)

        # Prioridade
        ttk.Label(card, text="Prioridade", style="Subheading.TLabel").grid(
            row=4, column=0, sticky="w", padx=(0, 16), pady=6
        )
        self.priority_combo = ttk.Combobox(
            card,
            state="disabled",
            width=38,
            values=tuple(self.priority_by_label),
        )
        self.priority_combo.grid(row=4, column=1, sticky="ew", pady=6)
        self.priority_combo.bind("<<ComboboxSelected>>", self.update_state)

        # Indicador de fila, estimativa de espera e pré-visualização
        info_frame = ttk.Frame(card, style="Surface.TFrame")
        info_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 2))
        info_frame.columnconfigure(0, weight=1)

        self.queue_info_label = ttk.Label(
            info_frame,
            text="Aguardando: 0 senha(s) • Estimativa de espera: ~0 min",
            style="Muted.TLabel",
        )
        self.queue_info_label.grid(row=0, column=0, sticky="w")

        self.preview_label = ttk.Label(
            info_frame,
            text="Prévia: —",
            style="Muted.TLabel",
        )
        self.preview_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Mensagem de status/erro
        self.message = MessageArea(card)
        self.message.grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 4))

        # Destaque da senha gerada
        ticket_box = ttk.LabelFrame(card, text="Senha emitida", padding=(20, 14))
        ticket_box.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(6, 16))
        ticket_box.columnconfigure(0, weight=1)

        self.ticket_label = ttk.Label(
            ticket_box,
            text="—",
            font=("Segoe UI", 32, "bold"),
            foreground="#0f4c81",
            anchor="center",
        )
        self.ticket_label.grid(row=0, column=0, sticky="ew", pady=(2, 2))

        self.ticket_info_label = ttk.Label(
            ticket_box,
            text="Aguardando emissão",
            style="Muted.TLabel",
            anchor="center",
        )
        self.ticket_info_label.grid(row=1, column=0, sticky="ew")

        # Botões de ação
        actions = ttk.Frame(card, style="Surface.TFrame")
        actions.grid(row=8, column=0, columnspan=2, sticky="ew")
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)

        create_button(
            actions,
            "Emitir senha",
            self.issue_ticket,
            0,
            0,
            style="Primary.TButton",
        )
        create_button(actions, "Limpar", self.clear, 0, 1)

        if self.specialties:
            self.specialty_combo.current(0)
        self.update_state()
        self._bind_shortcuts()

    def _bind_shortcuts(self) -> None:
        for idx in range(min(6, len(self.specialties))):
            self.bind_all(f"<F{idx + 1}>", lambda event, i=idx: self._select_specialty_index(i))
        self.bind_all("<KeyPress-n>", lambda event: self._select_type_key(TipoSenha.NORMAL.value, event))
        self.bind_all("<KeyPress-N>", lambda event: self._select_type_key(TipoSenha.NORMAL.value, event))
        self.bind_all("<KeyPress-p>", lambda event: self._select_type_key(TipoSenha.PREFERENCIAL.value, event))
        self.bind_all("<KeyPress-P>", lambda event: self._select_type_key(TipoSenha.PREFERENCIAL.value, event))

    def _select_specialty_index(self, index: int) -> None:
        if not self.winfo_exists():
            return
        if 0 <= index < len(self.specialties):
            self.specialty_combo.current(index)
            self.update_state()

    def _select_type_key(self, tipo_valor: str, event=None) -> None:
        if not self.winfo_exists():
            return
        widget = getattr(event, "widget", None)
        if isinstance(widget, (tk.Entry, ttk.Entry, tk.Text)):
            return
        for label, val in TIPO_OPCOES.items():
            if val == tipo_valor:
                self.type_combo.set(label)
                self.update_state()
                break

    def _refresh_queue_and_preview(self, specialty, ticket_type: str) -> None:
        if specialty is None or self.connection is None:
            self.queue_info_label.configure(
                text="Aguardando: 0 senha(s) • Estimativa de espera: ~0 min"
            )
            self.preview_label.configure(text="Prévia: —")
            return

        avg_minutes = getattr(specialty, "tempo_medio", None) or 30
        waiting_count = 0
        next_seq = 1

        try:
            cur = self.connection.cursor()
            row_wait = cur.execute(
                """
                SELECT COUNT(*) FROM senhas
                WHERE especialidade_id = ? AND LOWER(status) = 'aguardando'
                """,
                (specialty.id,),
            ).fetchone()
            if row_wait and row_wait[0] is not None:
                waiting_count = int(row_wait[0])

            today_prefix = datetime.now().strftime("%Y-%m-%d")
            cols = [r[1] for r in cur.execute("PRAGMA table_info(senhas)").fetchall()]
            if "criada_em" in cols:
                row_seq = cur.execute(
                    """
                    SELECT COUNT(*) FROM senhas
                    WHERE especialidade_id = ? AND tipo = ? AND criada_em LIKE ?
                    """,
                    (specialty.id, ticket_type, f"{today_prefix}%"),
                ).fetchone()
            else:
                row_seq = cur.execute(
                    """
                    SELECT COUNT(*) FROM senhas
                    WHERE especialidade_id = ? AND tipo = ?
                    """,
                    (specialty.id, ticket_type),
                ).fetchone()
            if row_seq and row_seq[0] is not None:
                next_seq = int(row_seq[0]) + 1
        except Exception:
            pass

        estimated_min = waiting_count * int(avg_minutes)
        self.queue_info_label.configure(
            text=f"Aguardando: {waiting_count} senha(s) • Estimativa de espera: ~{estimated_min} min"
        )
        preview_code = f"{specialty.codigo}-{ticket_type}-{next_seq:03d}"
        self.preview_label.configure(text=f"Prévia da próxima senha: {preview_code}")

    def update_state(self, event=None) -> None:
        selected_type = TIPO_OPCOES.get(self.type_combo.get(), TipoSenha.NORMAL.value)
        if selected_type == TipoSenha.PREFERENCIAL.value:
            self.priority_combo.configure(state="readonly")
            if not self.priority_combo.get():
                self.priority_combo.current(0)
        else:
            self.priority_combo.set("")
            self.priority_combo.configure(state="disabled")

        specialty = self.specialty_by_label.get(self.specialty_combo.get())
        self._refresh_queue_and_preview(specialty, selected_type)

    def issue_ticket(self) -> None:
        specialty = self.specialty_by_label.get(self.specialty_combo.get())
        if specialty is None:
            self.message.show("Selecione uma especialidade.", error=True)
            return

        ticket_type = TIPO_OPCOES.get(self.type_combo.get(), TipoSenha.NORMAL.value)
        priority = (
            self.priority_by_label.get(self.priority_combo.get())
            if ticket_type == TipoSenha.PREFERENCIAL.value
            else None
        )

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
        detalhe = f"{specialty.nome} • {'Preferencial (' + priority + ')' if priority else 'Normal'}"
        self.ticket_info_label.configure(text=detalhe)
        self.message.show("Senha emitida com sucesso.")
        self._refresh_queue_and_preview(specialty, ticket_type)

    def clear(self) -> None:
        self.ticket_label.configure(text="—")
        self.ticket_info_label.configure(text="Aguardando emissão")
        self.message.show("")
        self.type_combo.set("Normal (N)")
        self.update_state()


if __name__ == "__main__":
    from database.connection import Database
    from ui import theme

    root = tk.Tk()
    root.title("Recepção")
    root.geometry("640x520")
    theme.init(root)
    with Database(":memory:") as database:
        view = ReceptionView(root, database.connection)
        view.pack(fill="both", expand=True)
        root.mainloop()