"""Autenticação com hash de senha (PBKDF2-SHA256, apenas biblioteca padrão).

PROVISÓRIO: criado para destravar o login da interface. Alinhar com a Ingrid
(backend) e a Pessoa 3 (login/permissões) se vão manter, mover ou trocar.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from typing import Optional

from database.models import PerfilUsuario, Usuario
from database.repositories import UsuarioRepository

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 200_000

# Apenas para desenvolvimento: criados quando a tabela de usuários está vazia.
DEFAULT_PASSWORD = "senha123"
DEFAULT_USERS = (
    ("admin", PerfilUsuario.ADMINISTRADOR),
    ("recepcao", PerfilUsuario.RECEPCAO),
    ("profissional", PerfilUsuario.PROFISSIONAL),
    ("coordenacao", PerfilUsuario.COORDENACAO),
)


class AuthService:
    def __init__(self, connection: sqlite3.Connection):
        self.db = connection
        self.users = UsuarioRepository(connection)

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> str:
        salt = salt or secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), ITERATIONS
        ).hex()
        return f"{ALGORITHM}${ITERATIONS}${salt}${digest}"

    @staticmethod
    def verify_password(password: str, stored: str) -> bool:
        try:
            algorithm, iterations, salt, digest = stored.split("$")
            if algorithm != ALGORITHM:
                return False
            calculated = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations)
            ).hex()
        except (ValueError, TypeError):
            return False
        return hmac.compare_digest(calculated, digest)

    def authenticate(self, login: str, password: str) -> Optional[Usuario]:
        user = self.users.get_by_login(login.strip())
        if user is None or not user.ativo:
            return None
        return user if self.verify_password(password, user.senha_hash) else None

    def ensure_default_users(self) -> list[str]:
        """Cria os usuários de desenvolvimento se não houver nenhum. Devolve os logins."""
        total = self.db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        if total:
            return []
        created = []
        for login, perfil in DEFAULT_USERS:
            self.users.create(
                Usuario(
                    login=login,
                    senha_hash=self.hash_password(DEFAULT_PASSWORD),
                    perfil=perfil,
                )
            )
            created.append(login)
        return created
