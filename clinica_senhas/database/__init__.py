"""Camada de persistência do Sistema de Senhas da Clínica."""

from .connection import Database, initialize_database

__all__ = ["Database", "initialize_database"]

