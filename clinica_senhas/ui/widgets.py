"""Componentes reutilizáveis da interface do Sistema de Senhas.

Mantém a API que as telas já usam (ApplicationFrame, MessageArea, PasswordCard,
DataTable, create_button, labeled_entry) e acrescenta: PriorityBadge,
SpecialtyCard, ThemedListbox e AccessibilityBar.

Para ver todos os componentes:  python -m ui.widgets   (a partir da raiz)
"""
from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any, Callable, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ui import theme


class ApplicationFrame(ttk.Frame):
    def __init__(self, master: tk.Misc, title: str, **kwargs):
        theme.ensure(master)
        super().__init__(master, padding=16, **kwargs)
        self.columnconfigure(0, weight=1)
        self.title_label = ttk.Label(self, text=title, style="Title.TLabel")
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 16))


class MessageArea(ttk.Label):
    """Linha de mensagem: informação (azul), erro (vermelho) ou sucesso (verde)."""

    def __init__(self, master: tk.Misc, **kwargs):
        theme.ensure(master)
        kwargs.setdefault("style", "Info.TLabel")
        kwargs.setdefault("wraplength", 560)
        super().__init__(master, **kwargs)

    def show(self, message: str, error: bool = False, success: bool = False) -> None:
        if error:
            style = "Error.TLabel"
        elif success:
            style = "Success.TLabel"
        else:
            style = "Info.TLabel"
        self.configure(text=message, style=style)

    def clear(self) -> None:
        self.configure(text="", style="Info.TLabel")


class PriorityBadge(ttk.Label):
    """Selo colorido: 'Normal' para N ou o código (P1..P6) para preferenciais."""

    def __init__(
        self,
        master: tk.Misc,
        priority: Any = None,
        text: Optional[str] = None,
        **kwargs,
    ):
        theme.ensure(master)
        super().__init__(master, **kwargs)
        self.set(priority, text)

    def set(self, priority: Any = None, text: Optional[str] = None) -> None:
        key = theme.priority_key(priority)
        label = text or ("Normal" if key == "N" else key)
        self.configure(text=label, style=f"{key}.Badge.TLabel")


class PasswordCard(ttk.LabelFrame):
    """Cartão com a senha em destaque. ``priority`` (opcional) mostra o selo."""

    def __init__(self, master: tk.Misc, **kwargs):
        theme.ensure(master)
        super().__init__(master, text="Senha chamada", padding=16, **kwargs)
        self.code_label = ttk.Label(self, text="-", style="Ticket.TLabel")
        self.code_label.pack(pady=8)
        self.badge = PriorityBadge(self)
        self.details_label = ttk.Label(self, text="", style="Heading.TLabel")
        self.details_label.pack()

    def show(self, code: str, details: str = "", priority: Any = None) -> None:
        """Mostra a senha. Passe priority='N' ou 'P1'... para exibir o selo."""
        self.code_label.configure(text=code)
        self.details_label.configure(text=details)
        if priority is None:
            self.badge.pack_forget()
        else:
            self.badge.set(priority)
            self.badge.pack(before=self.details_label, pady=(0, 6))


class DataTable(ttk.Treeview):
    def __init__(self, master: tk.Misc, columns: tuple[str, ...], **kwargs):
        theme.ensure(master)
        super().__init__(master, columns=columns, show="headings", **kwargs)
        for column in columns:
            self.heading(column, text=column.replace("_", " ").title())
            self.column(column, width=130, anchor="center")

    def clear(self) -> None:
        for item in self.get_children():
            self.delete(item)

    def add_row(self, values: tuple[object, ...]) -> None:
        self.insert("", "end", values=values)

    def selected_values(self) -> Optional[tuple]:
        selection = self.selection()
        if not selection:
            return None
        return tuple(self.item(selection[0], "values"))


class SpecialtyCard(ttk.Frame):
    """Cartão clicável de especialidade (código, nome, atalho e fila de espera)."""

    def __init__(
        self,
        master: tk.Misc,
        code: str,
        name: str,
        shortcut: Optional[str] = None,
        on_click: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        theme.ensure(master)
        super().__init__(master, style="Card.TFrame", padding=12, **kwargs)
        self.code = code
        self.on_click = on_click
        self._selected = False
        self.columnconfigure(0, weight=1)

        self.hint_label = ttk.Label(
            self, text=shortcut or "", style="Card.Hint.TLabel", anchor="e"
        )
        self.code_label = ttk.Label(
            self, text=code, style="Card.Code.TLabel", anchor="center"
        )
        self.name_label = ttk.Label(
            self, text=name, style="Card.TLabel", anchor="center"
        )
        self.count_label = ttk.Label(
            self, text="", style="Card.Hint.TLabel", anchor="center"
        )
        self.hint_label.grid(row=0, column=0, sticky="ew")
        self.code_label.grid(row=1, column=0, sticky="ew")
        self.name_label.grid(row=2, column=0, sticky="ew")
        self.count_label.grid(row=3, column=0, sticky="ew")

        for widget in (self, self.hint_label, self.code_label,
                       self.name_label, self.count_label):
            widget.bind("<Button-1>", self._clicked)
            widget.configure(cursor="hand2")

    def _clicked(self, event=None) -> None:
        self.activate()

    def activate(self) -> None:
        if self.on_click is not None:
            self.on_click(self.code)

    def set_waiting(self, amount: int) -> None:
        text = "Nenhuma aguardando" if amount == 0 else f"{amount} aguardando"
        self.count_label.configure(text=text)

    @property
    def selected(self) -> bool:
        return self._selected

    def select(self, selected: bool = True) -> None:
        self._selected = selected
        prefix = "CardSel" if selected else "Card"
        self.configure(style=f"{prefix}.TFrame")
        self.hint_label.configure(style=f"{prefix}.Hint.TLabel")
        self.code_label.configure(style=f"{prefix}.Code.TLabel")
        self.name_label.configure(style=f"{prefix}.TLabel")
        self.count_label.configure(style=f"{prefix}.Hint.TLabel")


class ThemedListbox(tk.Listbox):
    """Listbox (widget tk clássico) que acompanha o tema e o tamanho da fonte."""

    def __init__(self, master: tk.Misc, font_name: str = "heading", **kwargs):
        theme.ensure(master)
        self._font_name = font_name
        super().__init__(master, **kwargs)
        self._restyle()
        theme.subscribe(self._restyle)
        self.bind("<Destroy>", self._on_destroy, add="+")

    def _on_destroy(self, event) -> None:
        if event.widget is self:
            theme.unsubscribe(self._restyle)

    def _restyle(self) -> None:
        p = theme.palette()
        self.configure(
            background=p.surface,
            foreground=p.text,
            selectbackground=p.primary,
            selectforeground=p.on_primary,
            highlightthickness=1,
            highlightbackground=p.border,
            highlightcolor=p.primary,
            relief="flat",
            activestyle="none",
            font=theme.fname(self._font_name),
        )


class AccessibilityBar(ttk.Frame):
    """Barra com A−, A+ e Alto contraste (liga/desliga o tema de alto contraste)."""

    def __init__(self, master: tk.Misc, **kwargs):
        theme.ensure(master)
        super().__init__(master, **kwargs)
        self._contrast = tk.BooleanVar(value=theme.is_high_contrast())
        ttk.Button(self, text="A−", width=3, command=theme.decrease_font).grid(
            row=0, column=0, padx=2
        )
        ttk.Button(self, text="A+", width=3, command=theme.increase_font).grid(
            row=0, column=1, padx=2
        )
        ttk.Checkbutton(
            self,
            text="Alto contraste",
            variable=self._contrast,
            command=lambda: theme.set_high_contrast(self._contrast.get()),
        ).grid(row=0, column=2, padx=(8, 0))
        theme.subscribe(self._sync)
        self.bind("<Destroy>", self._on_destroy, add="+")

    def _sync(self) -> None:
        self._contrast.set(theme.is_high_contrast())

    def _on_destroy(self, event) -> None:
        if event.widget is self:
            theme.unsubscribe(self._sync)


def create_button(
    master: tk.Misc,
    text: str,
    command: Callable[[], None],
    row: int,
    column: int = 0,
    style: Optional[str] = None,
    **kwargs,
) -> ttk.Button:
    """Cria um botão na grade. style: 'Primary.TButton', 'Danger.TButton',
    'Success.TButton' ou as versões grandes ('Big.Primary.TButton' etc.)."""
    if style:
        kwargs["style"] = style
    button = ttk.Button(master, text=text, command=command, **kwargs)
    button.grid(row=row, column=column, padx=4, pady=4, sticky="ew")
    return button


def labeled_entry(
    master: tk.Misc,
    label: str,
    row: int,
    show: Optional[str] = None,
) -> ttk.Entry:
    ttk.Label(master, text=label).grid(row=row, column=0, sticky="w", pady=4)
    entry = ttk.Entry(master, show=show)
    entry.grid(row=row, column=1, sticky="ew", pady=4)
    return entry


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Componentes - Sistema de Senhas")
    root.geometry("900x720")
    theme.init(root)

    frame = ApplicationFrame(root, "Galeria de componentes")
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(1, weight=1)

    AccessibilityBar(frame).grid(row=1, column=0, sticky="w", pady=(0, 8))

    message = MessageArea(frame)
    message.grid(row=2, column=0, columnspan=3, sticky="w")
    message.show("Mensagem de informação.")

    buttons = ttk.Frame(frame)
    buttons.grid(row=3, column=0, columnspan=3, sticky="ew", pady=8)
    for col in range(4):
        buttons.columnconfigure(col, weight=1)
    create_button(buttons, "Padrão", lambda: message.show("Padrão"), 0, 0)
    create_button(buttons, "Primário", lambda: message.show("Ok", success=True),
                  0, 1, style="Primary.TButton")
    create_button(buttons, "Sucesso", lambda: message.show("Sucesso", success=True),
                  0, 2, style="Success.TButton")
    create_button(buttons, "Perigo", lambda: message.show("Erro!", error=True),
                  0, 3, style="Danger.TButton")
    create_button(buttons, "Senha normal", lambda: None, 1, 0, 2,
                  style="Big.Primary.TButton")
    create_button(buttons, "Senha preferencial", lambda: None, 1, 2, 2,
                  style="Big.Success.TButton")

    badges = ttk.Frame(frame)
    badges.grid(row=4, column=0, columnspan=3, sticky="w", pady=4)
    for index, key in enumerate((None, "P1", "P2", "P3", "P4", "P5", "P6")):
        PriorityBadge(badges, key).grid(row=0, column=index, padx=3)

    cards = ttk.Frame(frame)
    cards.grid(row=5, column=0, columnspan=3, sticky="ew", pady=8)
    card_list: list[SpecialtyCard] = []

    def pick(code: str) -> None:
        for card in card_list:
            card.select(card.code == code)
        message.show(f"Especialidade selecionada: {code}")

    for index, (code, name) in enumerate(
        (("CG", "Clínico geral"), ("PSI", "Psicologia"), ("PED", "Pediatria"))
    ):
        cards.columnconfigure(index, weight=1)
        card = SpecialtyCard(cards, code, name, f"F{index + 1}", pick)
        card.set_waiting(index * 2)
        card.grid(row=0, column=index, padx=4, sticky="nsew")
        card_list.append(card)

    password = PasswordCard(frame)
    password.grid(row=6, column=0, columnspan=3, sticky="ew", pady=8)
    password.show("CG-P-023", "Consultório 01", priority="P1")

    listbox = ThemedListbox(frame, height=3)
    listbox.grid(row=7, column=0, columnspan=3, sticky="ew")
    for item in ("CG-P-023 - Consultório 01", "PED-N-007 - Consultório 08"):
        listbox.insert(tk.END, item)

    table = DataTable(frame, ("id", "codigo", "nome"), height=3)
    table.grid(row=8, column=0, columnspan=3, sticky="ew", pady=8)
    table.add_row((1, "CG", "Clínico geral"))
    table.add_row((2, "PSI", "Psicologia"))

    root.mainloop()