from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


class BackupService:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

    def create_backup(
        self,
        backup_directory: str | Path,
        prefix: str = "clinic",
    ) -> Path:
        if not self.database_path.exists():
            raise FileNotFoundError(f"Banco não encontrado: {self.database_path}")
        directory = Path(backup_directory)
        directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        destination = directory / f"{prefix}_{timestamp}.db"
        source_connection = sqlite3.connect(self.database_path)
        destination_connection = sqlite3.connect(destination)
        try:
            source_connection.backup(destination_connection)
            destination_connection.commit()
        finally:
            destination_connection.close()
            source_connection.close()
        return destination

    def restore_backup(self, backup_path: str | Path) -> None:
        backup = Path(backup_path)
        if not backup.exists():
            raise FileNotFoundError(f"Backup não encontrado: {backup}")
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        source_connection = sqlite3.connect(backup)
        destination_connection = sqlite3.connect(self.database_path)
        try:
            source_connection.backup(destination_connection)
            destination_connection.commit()
        finally:
            destination_connection.close()
            source_connection.close()

    def list_backups(self, backup_directory: str | Path) -> list[Path]:
        directory = Path(backup_directory)
        if not directory.exists():
            return []
        return sorted(directory.glob("*.db"), reverse=True)


if __name__ == "__main__":
    print("BackupService pronto")

