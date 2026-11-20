from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional


class AuditService:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self._create_table()

    def _create_table(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                acao TEXT NOT NULL,
                entidade TEXT,
                entidade_id INTEGER,
                detalhes TEXT,
                criado_em TEXT NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
            """
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_auditoria_criado_em ON auditoria(criado_em)"
        )
        self.connection.commit()

    def record(
        self,
        action: str,
        entity: Optional[str] = None,
        entity_id: Optional[int] = None,
        details: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> int:
        if not action.strip():
            raise ValueError("A ação é obrigatória")
        cursor = self.connection.execute(
            """
            INSERT INTO auditoria
                (usuario_id, acao, entidade, entidade_id, detalhes, criado_em)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                action.strip(),
                entity,
                entity_id,
                details,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def list_recent(self, limit: int = 100) -> list[sqlite3.Row]:
        if limit < 1:
            raise ValueError("O limite deve ser maior que zero")
        cursor = self.connection.execute(
            """
            SELECT id, usuario_id, acao, entidade, entidade_id, detalhes, criado_em
            FROM auditoria
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cursor.fetchall()


if __name__ == "__main__":
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    service = AuditService(connection)
    service.record("Inicialização")
    print(len(service.list_recent()))
    connection.close()

