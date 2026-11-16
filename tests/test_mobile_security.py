import hashlib
import importlib
import sqlite3
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch


class PruebaSesionesMoviles(unittest.TestCase):
    def setUp(self):
        with patch.dict(sys.modules, {"scripts_db.db_conexion": Mock()}):
            self.auth = importlib.import_module("scripts_db.autenticacion")

        self.bd = sqlite3.connect(":memory:")
        self.addCleanup(self.bd.close)
        self.bd.execute(
            "CREATE TABLE sesiones_movil "
            "(token_hash TEXT PRIMARY KEY, id_usuario INTEGER, expira TEXT)"
        )

        self.token = "token-de-prueba"
        self.expira = datetime(2030, 1, 1, 12, 10)
        token_hash = hashlib.sha256(self.token.encode("utf-8")).hexdigest()
        self.bd.execute(
            "INSERT INTO sesiones_movil VALUES (?, ?, ?)",
            (token_hash, 7, self.expira.isoformat(" ")),
        )

        parche = patch.object(self.auth, "conectar_bd", self.conectar)
        parche.start()
        self.addCleanup(parche.stop)

    def conectar(self):
        cursor_sqlite = self.bd.cursor()
        cursor = Mock(wraps=cursor_sqlite)

        def ejecutar(sql, parametros):
            valores = tuple(
                valor.isoformat(" ") if isinstance(valor, datetime) else valor
                for valor in parametros
            )
            cursor_sqlite.execute(sql.replace("%s", "?"), valores)
            cursor.rowcount = cursor_sqlite.rowcount

        cursor.execute.side_effect = ejecutar
        conexion = Mock()
        conexion.cursor.return_value = cursor
        conexion.commit.side_effect = self.bd.commit
        return conexion

    def test_token_vigente_devuelve_el_usuario(self):
        ahora = self.expira - timedelta(seconds=1)
        self.assertEqual(self.auth.validar_sesion(self.token, ahora=ahora), 7)

    def test_token_vence_en_el_instante_de_expiracion(self):
        self.assertIsNone(self.auth.validar_sesion(self.token, ahora=self.expira))

    def test_cerrar_sesion_revoca_un_token_aun_vigente(self):
        ahora = self.expira - timedelta(seconds=1)
        self.assertEqual(self.auth.validar_sesion(self.token, ahora=ahora), 7)
        self.assertEqual(self.auth.cerrar_sesion(self.token), 1)
        self.assertIsNone(self.auth.validar_sesion(self.token, ahora=ahora))