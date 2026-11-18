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

        self.bd.execute(
            "CREATE TABLE usuarios "
            "(id_usuario INTEGER PRIMARY KEY, identificador TEXT, clave_hash TEXT, activo BOOLEAN)"
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

        def obtener_cursor(dictionary=False):
            cursor_sqlite.row_factory = sqlite3.Row if dictionary else None
            return cursor

        conexion = Mock()
        conexion.cursor.side_effect = obtener_cursor
        conexion.commit.side_effect = self.bd.commit
        return conexion

    def test_inicio_con_clave_emite_un_token_y_solo_guarda_su_hash(self):
        self.bd.execute(
            "INSERT INTO usuarios VALUES (?, ?, ?, ?)",
            (8, "prueba", self.auth.hashear_clave("clave-prueba"), True),
        )
        sesion = self.auth.iniciar_sesion("prueba", "clave-prueba")
        self.assertIsNotNone(sesion)
        self.assertEqual(self.auth.validar_sesion(sesion["token"]), 8)
        fila = self.bd.execute(
            "SELECT token_hash FROM sesiones_movil WHERE id_usuario = ?", (8,)
        ).fetchone()
        self.assertEqual(fila[0], hashlib.sha256(sesion["token"].encode()).hexdigest())

    def test_emision_rechaza_una_cuenta_que_dejo_de_estar_activa(self):
        self.bd.execute(
            "INSERT INTO usuarios VALUES (?, ?, ?, ?)",
            (8, "prueba", self.auth.hashear_clave("clave-prueba"), True),
        )
        verificar = self.auth._verificar

        def verificar_y_desactivar(hash_guardado, clave):
            resultado = verificar(hash_guardado, clave)
            self.bd.execute("UPDATE usuarios SET activo = FALSE WHERE id_usuario = ?", (8,))
            return resultado

        with patch.object(self.auth, "_verificar", side_effect=verificar_y_desactivar):
            self.assertIsNone(self.auth.iniciar_sesion("prueba", "clave-prueba"))
        self.assertIsNone(
            self.bd.execute("SELECT 1 FROM sesiones_movil WHERE id_usuario = ?", (8,)).fetchone()
        )

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