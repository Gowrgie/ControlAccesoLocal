import os
import unittest
from unittest.mock import Mock, patch

from argon2 import PasswordHasher

from scripts_db import db_conexion_admin


class PruebaAltaAdministrativa(unittest.TestCase):
    def test_alta_guarda_la_clave_local_y_su_hash_movil(self):
        conexion = Mock()
        cursor = conexion.cursor.return_value
        cursor.fetchone.side_effect = [(2,), None]
        cursor.lastrowid = 42

        with patch.object(db_conexion_admin, "conectar_bd_admin", return_value=conexion):
            id_usuario = db_conexion_admin.crear_usuario_admin("Diego", "1212", "123123", 2)

        self.assertEqual(id_usuario, 42)
        consulta, parametros = cursor.execute.call_args.args
        self.assertIn("clave_acceso, clave_hash", consulta)
        nombre, identificador, clave, clave_hash, id_rol = parametros
        self.assertEqual((nombre, identificador, clave, id_rol), ("Diego", "1212", "123123", 2))
        self.assertTrue(PasswordHasher().verify(clave_hash, clave))
        conexion.commit.assert_called_once_with()

    def test_conexion_usa_la_credencial_configurada(self):
        with patch.dict(os.environ, {db_conexion_admin.DB_PASSWORD_ENV: "clave-de-prueba"}):
            with patch.object(db_conexion_admin.mysql.connector, "connect") as conectar:
                db_conexion_admin.conectar_bd_admin()

        self.assertEqual(conectar.call_args.kwargs["user"], "control_acceso_admin")
        self.assertEqual(conectar.call_args.kwargs["password"], "clave-de-prueba")

    def test_conexion_sin_credencial_falla_sin_conectar(self):
        with patch.dict(os.environ, {db_conexion_admin.DB_PASSWORD_ENV: ""}):
            with patch.object(db_conexion_admin.mysql.connector, "connect") as conectar:
                with self.assertRaisesRegex(ValueError, db_conexion_admin.DB_PASSWORD_ENV):
                    db_conexion_admin.conectar_bd_admin()

        conectar.assert_not_called()
