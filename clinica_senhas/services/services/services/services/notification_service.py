from __future__ import annotations

import os
import sys
from typing import Callable, Optional


class NotificationService:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._listeners: list[Callable[[str], None]] = []

    def add_listener(self, listener: Callable[[str], None]) -> None:
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[str], None]) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def notify(self, message: str) -> bool:
        if not self.enabled:
            return False
        for listener in tuple(self._listeners):
            listener(message)
        return True

    def announce_ticket(
        self,
        codigo: str,
        consultorio: Optional[str] = None,
    ) -> bool:
        message = f"Senha {codigo}"
        if consultorio:
            message = f"{message}, dirigir-se ao consultório {consultorio}"
        notified = self.notify(message)
        if notified:
            self.beep()
        return notified

    @staticmethod
    def beep() -> None:
        if os.name == "nt":
            import winsound
            winsound.Beep(900, 180)
        else:
            sys.stdout.write("\a")
            sys.stdout.flush()


if __name__ == "__main__":
    service = NotificationService()
    service.add_listener(print)
    service.announce_ticket("CG-P-001", "01")

