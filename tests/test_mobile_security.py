import base64
import hashlib
import importlib
import sqlite3
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from api.app import crear_api


class PruebaSesionesMoviles(unittest.TestCase):
    def setUp(self):
        with patch.dict(sys.modules, {"scripts_db.db_conexion": Mock()}):
            self.auth = importlib.import_module("scripts_db.autenticacion")

        self.bd = sqlite3.connect(":memory:", check_same_thread=False)
        self.addCleanup(self.bd.close)
        self.bd.execute(
            "CREATE TABLE sesiones_movil "
            "(token_hash TEXT PRIMARY KEY, id_usuario INTEGER, expira TEXT)"
        )

        self.bd.execute(
            "CREATE TABLE usuarios "
            "(id_usuario INTEGER PRIMARY KEY, identificador TEXT, clave_hash TEXT, activo BOOLEAN)"
        )
        self.bd.execute(
            "CREATE TABLE credenciales_biometricas_movil "
            "(id_credencial TEXT PRIMARY KEY, id_usuario INTEGER, clave_publica BLOB)"
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

    def preparar_biometria(self):
        self.bd.execute(
            "INSERT INTO usuarios VALUES (?, ?, ?, ?)",
            (8, "biometria", self.auth.hashear_clave("clave-prueba"), True),
        )
        clave = ec.generate_private_key(ec.SECP256R1())
        publica = clave.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        credenciales = {
            "identificador": "biometria",
            "clave": "clave-prueba",
            "biometric_public_key": base64.b64encode(publica).decode(),
        }
        cliente = TestClient(crear_api())
        self.addCleanup(cliente.close)
        return cliente, clave, credenciales

    def pedir_reto(self, cliente, id_credencial):
        respuesta = cliente.post(
            "/sessions/biometric/challenge", json={"credential_id": id_credencial}
        )
        self.assertEqual(respuesta.status_code, 200)
        return respuesta.json()["challenge"]

    @staticmethod
    def firmar_reto(clave, reto):
        firma = clave.sign(reto.encode("ascii"), ec.ECDSA(hashes.SHA256()))
        return {"challenge": reto, "signature": base64.b64encode(firma).decode()}

    def test_biometria_vincula_por_clave_y_emite_sesion_con_firma_de_un_solo_uso(self):
        cliente, clave, datos = self.preparar_biometria()
        vinculo = cliente.post("/sessions", json=datos)
        self.assertEqual(vinculo.status_code, 200)
        id_credencial = vinculo.json()["biometric_credential_id"]

        reto = self.pedir_reto(cliente, id_credencial)
        firmado = self.firmar_reto(clave, reto)
        inicio = cliente.post("/sessions/biometric", json=firmado)
        self.assertEqual(inicio.status_code, 200)
        self.assertEqual(self.auth.validar_sesion(inicio.json()["token"]), 8)
        self.assertEqual(cliente.post("/sessions/biometric", json=firmado).status_code, 401)

    def test_biometria_rechaza_clave_alterna_y_cuenta_inactiva(self):
        cliente, clave, datos = self.preparar_biometria()
        id_credencial = cliente.post("/sessions", json=datos).json()["biometric_credential_id"]

        reto = self.pedir_reto(cliente, id_credencial)
        otra = ec.generate_private_key(ec.SECP256R1())
        respuesta = cliente.post("/sessions/biometric", json=self.firmar_reto(otra, reto))
        self.assertEqual(respuesta.status_code, 401)

        self.bd.execute("UPDATE usuarios SET activo = FALSE WHERE id_usuario = 8")
        reto = self.pedir_reto(cliente, id_credencial)
        respuesta = cliente.post("/sessions/biometric", json=self.firmar_reto(clave, reto))
        self.assertEqual(respuesta.status_code, 401)

    def test_no_vincula_biometria_con_contrasena_incorrecta(self):
        cliente, _, datos = self.preparar_biometria()
        datos["clave"] = "incorrecta"
        self.assertEqual(cliente.post("/sessions", json=datos).status_code, 401)
        self.assertIsNone(self.bd.execute("SELECT id_credencial FROM credenciales_biometricas_movil").fetchone())

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