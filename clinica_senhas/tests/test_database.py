from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.connection import Database
from database.models import Prioridade, Profissional, Senha, StatusSenha, TipoSenha
from database.repositories import (
    EspecialidadeRepository,
    ProfissionalRepository,
    SenhaRepository,
)
from domain.metrics_service import MetricsService
from domain.numbering_service import NumberingService
from domain.priority_service import PriorityService
from domain.queue_service import QueueService


class DatabaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "test.db"
        self.database = Database(self.database_path)
        self.database.initialize()
        self.connection = self.database.connection

    def tearDown(self) -> None:
        self.database.close()
        self.temporary_directory.cleanup()

    def get_specialty(self, code: str = "CG"):
        specialties = EspecialidadeRepository(self.connection).list()
        return next(item for item in specialties if item.codigo == code)

    def test_database_tables_and_seed(self) -> None:
        tables = {
            row["name"]
            for row in self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        expected = {
            "especialidades",
            "consultorios",
            "profissionais",
            "senhas",
            "atendimentos",
            "usuarios",
            "configuracoes",
        }
        self.assertTrue(expected.issubset(tables))
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM especialidades").fetchone()[0],
            6,
        )
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM consultorios").fetchone()[0],
            18,
        )
        self.assertEqual(
            self.connection.execute("PRAGMA foreign_keys").fetchone()[0],
            1,
        )

    def test_professional_limit(self) -> None:
        specialty = self.get_specialty()
        repository = ProfissionalRepository(self.connection)
        for number in range(3):
            repository.create(
                Profissional(
                    nome=f"Profissional {number}",
                    registro=f"REG-{number}",
                    especialidade_id=specialty.id,
                    consultorio_id=number + 1,
                )
            )
        with self.assertRaises(ValueError):
            repository.create(
                Profissional(
                    nome="Quarto profissional",
                    registro="REG-4",
                    especialidade_id=specialty.id,
                    consultorio_id=4,
                )
            )

    def test_password_type_and_priority(self) -> None:
        specialty = self.get_specialty()
        repository = SenhaRepository(self.connection)
        normal = Senha.nova(
            "CG-N-001",
            specialty.id,
            TipoSenha.NORMAL,
        )
        preferential = Senha.nova(
            "CG-P-002",
            specialty.id,
            TipoSenha.PREFERENCIAL,
            Prioridade.P1,
        )
        repository.create(normal)
        repository.create(preferential)
        with self.assertRaises(ValueError):
            Senha.nova(
                "CG-N-003",
                specialty.id,
                TipoSenha.NORMAL,
                Prioridade.P2,
            )
        with self.assertRaises(ValueError):
            Senha.nova(
                "CG-P-004",
                specialty.id,
                TipoSenha.PREFERENCIAL,
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO senhas
                    (codigo, especialidade_id, tipo, prioridade, criada_em)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("ERR-001", specialty.id, "N", "P1", datetime.now().isoformat()),
            )

    def test_priority_service(self) -> None:
        PriorityService.validar("N")
        PriorityService.validar("P", "P1")
        self.assertEqual(PriorityService.peso("P1"), 1)
        self.assertEqual(PriorityService.peso("P6"), 6)
        self.assertEqual(PriorityService.peso(None), 99)
        with self.assertRaises(ValueError):
            PriorityService.validar("X")
        with self.assertRaises(ValueError):
            PriorityService.validar("P")
        with self.assertRaises(ValueError):
            PriorityService.validar("N", "P1")

    def test_numbering_service(self) -> None:
        specialty = self.get_specialty()
        service = NumberingService(self.connection)
        moment = datetime(2026, 11, 20, 8, 0, 0)
        first = service.emitir(specialty.id, "CG", "N", agora=moment)
        second = service.emitir(
            specialty.id,
            "CG",
            "P",
            "P1",
            agora=moment + timedelta(seconds=1),
        )
        self.assertEqual(first.codigo, "CG-N-001")
        self.assertEqual(second.codigo, "CG-P-002")

    def test_queue_order_and_transitions(self) -> None:
        specialty = self.get_specialty()
        professional = ProfissionalRepository(self.connection).create(
            Profissional(
                nome="Profissional de Teste",
                registro="TEST-001",
                especialidade_id=specialty.id,
                consultorio_id=1,
            )
        )
        numbering = NumberingService(self.connection)
        moment = datetime(2026, 11, 20, 9, 0, 0)
        p1 = numbering.emitir(specialty.id, "CG", "P", "P1", moment)
        normal = numbering.emitir(
            specialty.id,
            "CG",
            "N",
            agora=moment + timedelta(seconds=1),
        )
        p2 = numbering.emitir(
            specialty.id,
            "CG",
            "P",
            "P2",
            agora=moment + timedelta(seconds=2),
        )
        numbering.emitir(
            specialty.id,
            "CG",
            "N",
            agora=moment + timedelta(seconds=3),
        )
        queue = QueueService(self.connection)
        self.assertEqual(queue.chamar_proxima(specialty.id).codigo, p1.codigo)
        self.assertEqual(queue.chamar_proxima(specialty.id).codigo, p2.codigo)
        self.assertEqual(queue.chamar_proxima(specialty.id).codigo, normal.codigo)
        called = queue.chamar_proxima(specialty.id)
        attendance = queue.iniciar_atendimento(called.id, professional.id)
        queue.finalizar_atendimento(attendance.id, "Concluído")
        final_password = queue.senhas.get(called.id)
        self.assertEqual(final_password.status.value, "Finalizada")

    def test_metrics_service(self) -> None:
        specialty = self.get_specialty()
        professional = ProfissionalRepository(self.connection).create(
            Profissional(
                nome="Profissional de Métricas",
                registro="TEST-002",
                especialidade_id=specialty.id,
                consultorio_id=1,
            )
        )
        numbering = NumberingService(self.connection)
        queue = QueueService(self.connection)
        password = numbering.emitir(specialty.id, "CG", "N")
        queue.transicionar(password.id, StatusSenha.CHAMANDO)
        attendance = queue.iniciar_atendimento(password.id, professional.id)
        queue.finalizar_atendimento(attendance.id, "Concluído")
        start = datetime(2026, 11, 20, 10, 0, 0)
        end = start + timedelta(minutes=30)
        self.connection.execute(
            "UPDATE atendimentos SET inicio = ?, fim = ? WHERE id = ?",
            (start.isoformat(), end.isoformat(), attendance.id),
        )
        self.connection.commit()
        result = MetricsService(self.connection).calcular()
        self.assertEqual(result.atendimentos_finalizados, 1)
        self.assertEqual(result.media_geral_minutos, 30.0)
        self.assertEqual(result.media_por_especialidade["CG"], 30.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

