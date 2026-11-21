from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from typing import Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _round_rect_points(x1: int, y1: int, x2: int, y2: int, r: int = 20) -> list[int]:
    r = max(4, min(r, (x2 - x1) // 2, (y2 - y1) // 2))
    return [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]


class DisplayView(tk.Frame):
    """Painel público unificado em um cartão único com senha atual e histórico."""

    def __init__(self, master: tk.Misc, connection=None, **kwargs):
        super().__init__(master, highlightthickness=0, borderwidth=0, **kwargs)
        self.connection = connection

        self._bg_color = "#e8f2fc"
        self._card_bg = "#f7fbff"
        self._card_border = "#b8d4ee"
        self._accent = "#0f4c81"
        self._text = "#1e293b"
        self._muted = "#64748b"

        self.configure(bg=self._bg_color)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = tk.Frame(self, bg=self._bg_color)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(14, 6))
        header.columnconfigure(0, weight=1)

        tk.Label(
            header,
            text="Painel de chamadas",
            font=("Segoe UI", 17, "bold"),
            fg=self._accent,
            bg=self._bg_color,
        ).grid(row=0, column=0, sticky="w")

        tk.Button(
            header,
            text="Atualizar",
            font=("Segoe UI", 10, "bold"),
            fg=self._accent,
            bg="#ffffff",
            activebackground="#dbeafe",
            activeforeground=self._accent,
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.load_from_database,
        ).grid(row=0, column=1, sticky="e")

        self.canvas = tk.Canvas(
            self,
            bg=self._bg_color,
            highlightthickness=0,
            borderwidth=0,
        )
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=24, pady=(4, 20))
        self.canvas.bind("<Configure>", self._redraw_card)

        self.inner = tk.Frame(self.canvas, bg=self._card_bg)
        self._win_id = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")

        tk.Label(
            self.inner,
            text="SENHA CHAMADA",
            font=("Segoe UI", 10, "bold"),
            fg=self._muted,
            bg=self._card_bg,
        ).pack(pady=(6, 0))

        self.code_label = tk.Label(
            self.inner,
            text="—",
            font=("Segoe UI", 40, "bold"),
            fg=self._accent,
            bg=self._card_bg,
        )
        self.code_label.pack(pady=(2, 0))

        self.office_label = tk.Label(
            self.inner,
            text="Aguardando chamada",
            font=("Segoe UI", 12),
            fg=self._text,
            bg=self._card_bg,
        )
        self.office_label.pack(pady=(0, 12))

        tk.Frame(self.inner, height=1, bg="#dbeafe").pack(fill="x", padx=12, pady=(0, 10))

        tk.Label(
            self.inner,
            text="Últimas chamadas",
            font=("Segoe UI", 11, "bold"),
            fg=self._accent,
            bg=self._card_bg,
        ).pack(anchor="w", padx=12, pady=(0, 6))

        self.history = tk.Listbox(
            self.inner,
            height=6,
            font=("Segoe UI", 12),
            bg="#ffffff",
            fg=self._text,
            relief="flat",
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            selectbackground=self._accent,
            selectforeground="#ffffff",
        )
        self.history.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self.load_from_database()

    def _redraw_card(self, event=None) -> None:
        w = max(self.canvas.winfo_width(), 1)
        h = max(self.canvas.winfo_height(), 1)
        self.canvas.delete("card")
        if w > 12 and h > 12:
            pts = _round_rect_points(4, 4, w - 4, h - 4, r=22)
            self.canvas.create_polygon(
                pts,
                smooth=True,
                fill=self._card_bg,
                outline=self._card_border,
                width=2,
                tags="card",
            )
        self.canvas.coords(self._win_id, 16, 14)
        self.canvas.itemconfigure(
            self._win_id,
            width=max(w - 32, 120),
            height=max(h - 28, 120),
        )

    def load_from_database(self) -> None:
        if self.connection is None:
            return
        try:
            cur = self.connection.cursor()
            rows = cur.execute(
                """
                SELECT
                    s.codigo,
                    s.status,
                    e.nome,
                    p.consultorio_id
                FROM senhas s
                LEFT JOIN especialidades e ON e.id = s.especialidade_id
                LEFT JOIN profissionais p ON p.especialidade_id = s.especialidade_id AND p.ativo = 1
                WHERE LOWER(s.status) != 'aguardando'
                ORDER BY s.id DESC
                LIMIT 10
                """
            ).fetchall()

            cons_label_by_id: dict[int, str] = {}
            try:
                c_cols = [r[1] for r in cur.execute("PRAGMA table_info(consultorios)").fetchall()]
                label_col = next(
                    (col for col in ("nome", "codigo", "numero", "descricao") if col in c_cols),
                    None,
                )
                if label_col and "id" in c_cols:
                    for cid, clabel in cur.execute(f"SELECT id, {label_col} FROM consultorios").fetchall():
                        if clabel:
                            cons_label_by_id[cid] = str(clabel)
            except Exception:
                pass
        except Exception as exc:
            self.office_label.configure(text=f"Erro ao ler banco: {exc}")
            return

        if not rows:
            return

        destaque = None
        for r in rows:
            st = (r[1] or "").strip().lower()
            if st in ("chamando", "em atendimento", "em_atendimento"):
                destaque = r
                break
        if destaque is None:
            destaque = rows[0]

        codigo, status, esp_nome, cons_id = destaque
        cons_nome = cons_label_by_id.get(cons_id) if cons_id is not None else None

        partes = []
        if esp_nome:
            partes.append(esp_nome)
        if cons_nome:
            partes.append(f"Consultório {cons_nome}")
        if status:
            partes.append(status)

        self.code_label.configure(text=codigo)
        self.office_label.configure(text=" • ".join(partes) if partes else "Atendimento")

        self.history.delete(0, tk.END)
        seen = set()
        for codigo_h, status_h, esp_h, cons_h_id in rows:
            chave = (codigo_h, status_h)
            if chave in seen:
                continue
            seen.add(chave)
            cons_h_nome = cons_label_by_id.get(cons_h_id) if cons_h_id is not None else None
            info = " • ".join(
                [
                    x
                    for x in (
                        esp_h,
                        f"Consultório {cons_h_nome}" if cons_h_nome else None,
                        status_h,
                    )
                    if x
                ]
            )
            self.history.insert(tk.END, f"{codigo_h}  —  {info}" if info else codigo_h)
            if self.history.size() >= 8:
                break

    def show_call(self, code: str, office: Optional[str] = None) -> None:
        details = f"Consultório {office}" if office else "Atendimento"
        self.code_label.configure(text=code)
        self.office_label.configure(text=details)

        entry = f"{code}  —  {details}" if office else code
        self.history.insert(0, entry)
        if self.history.size() > 8:
            self.history.delete(8, tk.END)

    def clear_history(self) -> None:
        self.history.delete(0, tk.END)
        self.code_label.configure(text="—")
        self.office_label.configure(text="Aguardando chamada")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Painel público")
    root.geometry("800x600")
    view = DisplayView(root)
    view.pack(fill="both", expand=True)
    view.show_call("CAR-P-013", "01")
    root.mainloop()