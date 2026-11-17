"""LAC-101: conexión y operaciones del camino administrativo.

Usa la cuenta de MySQL control_acceso_admin (ver grant_admin_permissions.sql),
separada de la cuenta operativa control_acceso que usa db_conexion.py.
"""

import os

import mysql.connector

from scripts_db.autenticacion import hashear_clave

DB_HOST = "localhost"
DB_USER = "control_acceso_admin"
DB_PASSWORD_ENV = "CONTROL_ACCESO_ADMIN_DB_PASSWORD"
DB_NAME = "control_acceso"

TIEMPO_MAXIMO_CONEXION = 2


def conectar_bd_admin():
    password = os.environ.get(DB_PASSWORD_ENV)
    if not password:
        raise ValueError(f"Configura {DB_PASSWORD_ENV} para habilitar el alta de usuarios.")

    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=password,
        database=DB_NAME,
        connection_timeout=TIEMPO_MAXIMO_CONEXION,
    )


def crear_usuario_admin(nombre, identificador, clave_acceso, id_rol):
    """Crea un usuario activo y devuelve su id_usuario (camino administrativo)."""
    nombre = str(nombre or "").strip()
    identificador = str(identificador or "").strip()
    clave_acceso = str(clave_acceso or "")

    if not nombre or not identificador or not clave_acceso:
        raise ValueError("Completa el nombre, identificador y contraseña.")

    try:
        id_rol = int(id_rol)
    except (TypeError, ValueError):
        raise ValueError("Selecciona un rol válido.")

    conexion = conectar_bd_admin()
    cursor = None

    try:
        cursor = conexion.cursor()

        cursor.execute(
            "SELECT id_rol FROM roles WHERE id_rol = %s",
            (id_rol,),
        )
        if cursor.fetchone() is None:
            raise ValueError("El rol seleccionado no existe.")

        cursor.execute(
            "SELECT id_usuario FROM usuarios WHERE identificador = %s",
            (identificador,),
        )
        if cursor.fetchone() is not None:
            raise ValueError("Ese identificador ya está registrado.")

        cursor.execute(
            """
            INSERT INTO usuarios
                (nombre, identificador, clave_acceso, clave_hash, id_rol, activo)
            VALUES (%s, %s, %s, %s, %s, 1)
            """,
            (nombre, identificador, clave_acceso, hashear_clave(clave_acceso), id_rol),
        )
        conexion.commit()
        return cursor.lastrowid

    except mysql.connector.IntegrityError as error:
        conexion.rollback()
        if error.errno == 1062:
            raise ValueError("Ese identificador ya está registrado.") from error
        raise
    except Exception:
        conexion.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()
