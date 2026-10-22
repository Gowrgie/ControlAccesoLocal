"""Test for scripts_db/database.py (LAC-71).

It runs the insert, read and delete functions against the real MySQL database,
with the restricted user configured in db_conexion.py.

Requirements:
    - MySQL running with db_squema.sql and add_biometric_table.sql applied
    - grant_delete_embeddings.sql applied (otherwise the test stops at the start with a clear message)
    - at least one user in `usuarios` that has no face samples yet

Run it from the src/ folder:
    python -m unittest scripts_db.test_database -v

The test only deletes the rows it creates (model name "test-model"). If a
cleanup fails, those rows stay in the table and an administrator can remove
them with: DELETE FROM embeddings_faciales WHERE modelo = 'test-model';
"""
import unittest

import mysql.connector

from scripts_db import database
from scripts_db.db_conexion import conectar_bd

MODELO_PRUEBA = "test-model"
BYTES_PRUEBA = bytes(range(16))
MENSAJE_SIN_PERMISOS = ("The restricted user needs INSERT and DELETE on embeddings_faciales. Apply "
                        "src/scripts_db/add_biometric_table.sql and src/scripts_db/grant_delete_embeddings.sql "
                        "with an admin account.")


class PruebaEmbeddings(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # A user without samples: the "delete all" test can never erase real data.
        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute(
                "SELECT u.id_usuario FROM usuarios u "
                "LEFT JOIN embeddings_faciales e ON e.id_usuario = u.id_usuario "
                "WHERE e.id_embedding IS NULL ORDER BY u.id_usuario LIMIT 1"
            )
            fila = cursor.fetchone()
            cursor.close()
            conexion.close()
        except mysql.connector.Error as error:
            raise unittest.SkipTest(f"MySQL is not available: {error}")
        if fila is None:
            raise unittest.SkipTest("There is no user without face samples to test with")
        cls.id_usuario = fila[0]

        # Fail fast, without leaving rows behind, if INSERT or DELETE is missing:
        # a probe row is inserted and deleted inside a transaction that is always rolled back.
        conexion = conectar_bd()
        try:
            cursor = conexion.cursor()
            cursor.execute(
                "INSERT INTO embeddings_faciales (id_usuario, embedding, modelo) VALUES (%s, %s, %s)",
                (cls.id_usuario, BYTES_PRUEBA, MODELO_PRUEBA)
            )
            cursor.execute(
                "DELETE FROM embeddings_faciales WHERE id_usuario = %s AND modelo = %s",
                (cls.id_usuario, MODELO_PRUEBA)
            )
        except mysql.connector.ProgrammingError as error:
            if error.errno == 1142:  # command denied
                raise AssertionError(MENSAJE_SIN_PERMISOS)
            raise
        finally:
            conexion.rollback()
            conexion.close()

    def setUp(self):
        self.ids_creados = []

    def tearDown(self):
        for id_embedding in self.ids_creados:
            try:
                database.eliminar_embedding(id_embedding)
            except mysql.connector.Error as error:
                print(f"\nWARNING: could not clean up id_embedding={id_embedding}: {error}")

    def insertar(self, modelo=MODELO_PRUEBA, datos=BYTES_PRUEBA):
        id_embedding = database.insertar_embedding(self.id_usuario, datos, modelo)
        self.ids_creados.append(id_embedding)
        return id_embedding

    # ---- the connection really is the restricted user ----
    def test_usa_el_usuario_restringido(self):
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute("SELECT CURRENT_USER()")
        usuario = cursor.fetchone()[0]
        conexion.close()
        self.assertTrue(usuario.startswith("control_acceso@"), usuario)

    # ---- insert and read ----
    def test_insertar_y_leer(self):
        id_embedding = self.insertar()
        self.assertIsInstance(id_embedding, int)
        filas = database.leer_embeddings_usuario(self.id_usuario)
        fila = [f for f in filas if f["id_embedding"] == id_embedding][0]
        self.assertEqual(bytes(fila["embedding"]), BYTES_PRUEBA)
        self.assertEqual(fila["modelo"], MODELO_PRUEBA)
        self.assertIsNotNone(fila["fecha_registro"])

    def test_un_usuario_puede_tener_varias_muestras(self):
        primero = self.insertar()
        segundo = self.insertar(datos=bytes(reversed(BYTES_PRUEBA)))
        ids = [f["id_embedding"] for f in database.leer_embeddings_usuario(self.id_usuario)]
        self.assertEqual(ids, [primero, segundo])

    def test_usuario_inexistente_es_rechazado(self):
        with self.assertRaises(mysql.connector.IntegrityError):
            database.insertar_embedding(999999999, BYTES_PRUEBA, MODELO_PRUEBA)

    def test_leer_usuario_sin_muestras(self):
        self.assertEqual(database.leer_embeddings_usuario(self.id_usuario), [])

    # ---- delete ----
    def test_eliminar_una_muestra(self):
        id_embedding = self.insertar()
        self.assertEqual(database.eliminar_embedding(id_embedding), 1)
        ids = [f["id_embedding"] for f in database.leer_embeddings_usuario(self.id_usuario)]
        self.assertNotIn(id_embedding, ids)
        self.assertEqual(database.eliminar_embedding(id_embedding), 0)

    def test_eliminar_todas_las_muestras_del_usuario(self):
        self.insertar()
        self.insertar()
        self.assertEqual(database.eliminar_embeddings_usuario(self.id_usuario), 2)
        self.assertEqual(database.leer_embeddings_usuario(self.id_usuario), [])

    # ---- argument checks (nothing is written) ----
    def test_argumentos_invalidos(self):
        for datos, modelo in ((b"", MODELO_PRUEBA), ("texto", MODELO_PRUEBA), (None, MODELO_PRUEBA),
                              (BYTES_PRUEBA, ""), (BYTES_PRUEBA, "x" * 51), (BYTES_PRUEBA, None)):
            with self.assertRaises(ValueError):
                database.insertar_embedding(self.id_usuario, datos, modelo)
        self.assertEqual(database.leer_embeddings_usuario(self.id_usuario), [])


if __name__ == "__main__":
    unittest.main()