from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class PrintService:
    def format_ticket(
        self,
        codigo: str,
        especialidade: str = "",
        consultorio: Optional[str] = None,
    ) -> str:
        lines = ["SISTEMA DE SENHAS", "", f"SENHA: {codigo}"]
        if especialidade:
            lines.append(f"ESPECIALIDADE: {especialidade}")
        if consultorio:
            lines.append(f"CONSULTORIO: {consultorio}")
        lines.append("")
        return "\n".join(lines)

    def save_ticket(
        self,
        output_path: str | Path,
        codigo: str,
        especialidade: str = "",
        consultorio: Optional[str] = None,
    ) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            self.format_ticket(codigo, especialidade, consultorio),
            encoding="utf-8",
        )
        return path

    def print_ticket(
        self,
        codigo: str,
        especialidade: str = "",
        consultorio: Optional[str] = None,
        printer: Optional[str] = None,
    ) -> bool:
        content = self.format_ticket(codigo, especialidade, consultorio)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".txt",
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary_path = Path(temporary.name)
        try:
            if os.name == "nt":
                os.startfile(str(temporary_path), "print")
                return True
            command = ["lp"]
            if printer:
                command.extend(["-d", printer])
            command.append(str(temporary_path))
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
            return completed.returncode == 0
        except (FileNotFoundError, OSError):
            return False
        finally:
            try:
                temporary_path.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    service = PrintService()
    print(service.format_ticket("CG-N-001", "Clinico Geral", "01"))
