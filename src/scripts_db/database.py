"""Database module for facial embeddings: insert, read and delete.

Every function opens its own connection with conectar_bd() from db_conexion.py,
so it runs with the restricted MySQL user configured there
(DB_USER = "control_acceso"). MySQL errors (mysql.connector.Error) are not
caught here: the caller decides what to do with them, for example
validar_acceso_facial() turns them into "error_sistema".

Privileges the restricted user needs on embeddings_faciales:
    SELECT, INSERT  -> add_biometric_table.sql (LAC-53)
    DELETE          -> grant_delete_embeddings.sql (LAC-71)

Public interface:
    insertar_embedding(id_usuario, embedding_bytes, modelo) -> int
    leer_embeddings_usuario(id_usuario) -> list[dict]
    eliminar_embedding(id_embedding) -> int
    eliminar_embeddings_usuario(id_usuario) -> int

An embedding is stored as raw bytes. With numpy:
    embedding_bytes = vector.astype(numpy.float32).tobytes()
    vector = numpy.frombuffer(blob, dtype=numpy.float32)
"""
from scripts_db.db_conexion import conectar_bd

LARGO_MAXIMO_MODELO = 50  # embeddings_faciales.modelo is VARCHAR(50)


def _validar_muestra(embedding_bytes, modelo):
    if not isinstance(embedding_bytes, (bytes, bytearray)) or len(embedding_bytes) == 0:
        raise ValueError("El embedding debe ser un bloque de bytes no vacio")
    if not isinstance(modelo, str) or not modelo or len(modelo) > LARGO_MAXIMO_MODELO:
        raise ValueError(f"El modelo debe ser un texto de 1 a {LARGO_MAXIMO_MODELO} caracteres")


def insertar_embedding(id_usuario, embedding_bytes, modelo):
    """Stores one face sample for exactly one user. Returns the new id_embedding.

    The foreign key rejects an id_usuario that does not exist
    (mysql.connector.IntegrityError). Read faces for matching through
    cargar_embeddings_activos() in db_conexion.py, not from here."""
    _validar_muestra(embedding_bytes, modelo)
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO embeddings_faciales (id_usuario, embedding, modelo) VALUES (%s, %s, %s)",
            (id_usuario, bytes(embedding_bytes), modelo)
        )
        conexion.commit()
        id_embedding = cursor.lastrowid
        cursor.close()
        return id_embedding
    finally:
        conexion.close()


def leer_embeddings_usuario(id_usuario):
    """All the samples of one user, oldest first. Each item is a dict with
    id_embedding, embedding (bytes), modelo and fecha_registro.

    It reads the table directly, so it also returns the samples of a
    deactivated user. Face matching must use the active view instead."""
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_embedding, embedding, modelo, fecha_registro "
            "FROM embeddings_faciales WHERE id_usuario = %s ORDER BY id_embedding",
            (id_usuario,)
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        conexion.close()


def eliminar_embedding(id_embedding):
    """Deletes one sample. Returns how many rows were deleted (0 if it did not exist)."""
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM embeddings_faciales WHERE id_embedding = %s", (id_embedding,))
        conexion.commit()
        borrados = cursor.rowcount
        cursor.close()
        return borrados
    finally:
        conexion.close()


def eliminar_embeddings_usuario(id_usuario):
    """Deletes every sample of one user (for example before enrolling again).
    Returns how many rows were deleted."""
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM embeddings_faciales WHERE id_usuario = %s", (id_usuario,))
        conexion.commit()
        borrados = cursor.rowcount
        cursor.close()
        return borrados
    finally:
        conexion.close()