"""Authentication module for the mobile app (LAC-83).

Identifier + passcode are checked against an Argon2id hash, never against the
plaintext passcode. A valid login creates a short-lived session; it is not an
opening event: nothing here moves the servo, lights a LED or writes to
intentos_acceso.

It does not depend on any web framework: the API layer calls these functions.
It uses conectar_bd() from db_conexion.py, so it runs with the restricted user.

Public interface:
    hashear_clave(clave) -> str
    iniciar_sesion(identificador, clave) -> {"token": str, "expira": datetime} or None
    validar_sesion(token, ahora=None) -> id_usuario or None
    cerrar_sesion(token) -> int

iniciar_sesion returns None for EVERY failed login (unknown user, wrong
passcode, deactivated user, user without hash, malformed input), so the caller
cannot tell them apart and the response never reveals whether the user exists.
Database errors (mysql.connector.Error) are not caught: they are a system
failure, not an invalid credential, and the caller must report them as such.

Requires: pip install argon2-cffi
"""
import hashlib
import secrets
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

from scripts_db.db_conexion import conectar_bd

DURACION_SESION_MINUTOS = 10   # a session is short-lived
LARGO_MAXIMO_CLAVE = 128       # longer inputs are rejected before hashing

_hasher = PasswordHasher()  # Argon2id with the library defaults

# Verified when the user does not exist, so an unknown identifier costs the same
# time as a wrong passcode and the response time does not reveal the user.
_HASH_FALSO = _hasher.hash("clave-que-no-corresponde-a-nadie")


def hashear_clave(clave):
    """Argon2id hash of a passcode, ready to store in usuarios.clave_hash."""
    return _hasher.hash(clave)


def _verificar(hash_guardado, clave):
    try:
        return _hasher.verify(hash_guardado, clave)
    except (VerificationError, ValueError):  # mismatch or malformed hash
        return False


def _hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _emitir_sesion(conexion, cursor, id_usuario):
    """Crea una sesión para una identidad ya verificada que siga activa."""
    token = secrets.token_urlsafe(32)
    expira = datetime.now() + timedelta(minutes=DURACION_SESION_MINUTOS)
    cursor.execute(
        """
        INSERT INTO sesiones_movil (token_hash, id_usuario, expira)
        SELECT %s, id_usuario, %s FROM usuarios
        WHERE id_usuario = %s AND activo = TRUE
        """,
        (_hash_token(token), expira, id_usuario),
    )
    creada = cursor.rowcount == 1
    conexion.commit()
    if creada:
        return {"token": token, "expira": expira}
    return None


def iniciar_sesion(identificador, clave):
    """Valid credentials -> {"token", "expira"}. Anything else -> None."""
    if not isinstance(identificador, str) or not isinstance(clave, str):
        return None
    if not identificador or not clave or len(clave) > LARGO_MAXIMO_CLAVE:
        return None

    conexion = conectar_bd()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_usuario, clave_hash, activo FROM usuarios WHERE identificador = %s",
            (identificador,)
        )
        usuario = cursor.fetchone()

        # Always verify against some hash, existing user or not.
        hay_hash = usuario is not None and bool(usuario["clave_hash"])
        clave_correcta = _verificar(usuario["clave_hash"] if hay_hash else _HASH_FALSO, clave)

        try:
            if not hay_hash or not usuario["activo"] or not clave_correcta:
                return None
            return _emitir_sesion(conexion, cursor, usuario["id_usuario"])
        finally:
            cursor.close()
    finally:
        conexion.close()


def iniciar_sesion_usuario_verificado(id_usuario):
    """Emite una sesión para una identidad verificada por el servidor."""
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()
        try:
            return _emitir_sesion(conexion, cursor, id_usuario)
        finally:
            cursor.close()
    finally:
        conexion.close()


def validar_sesion(token, ahora=None):
    """id_usuario of a session that exists and has not expired, else None.
    ahora is only for tests; it defaults to the current time."""
    if not isinstance(token, str) or not token:
        return None
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT id_usuario FROM sesiones_movil WHERE token_hash = %s AND expira > %s",
            (_hash_token(token), ahora or datetime.now())
        )
        fila = cursor.fetchone()
        cursor.close()
        return fila[0] if fila else None
    finally:
        conexion.close()


def cerrar_sesion(token):
    """Deletes a session. Returns how many rows were deleted (0 if it did not exist)."""
    if not isinstance(token, str) or not token:
        return 0
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM sesiones_movil WHERE token_hash = %s", (_hash_token(token),))
        conexion.commit()
        borrados = cursor.rowcount
        cursor.close()
        return borrados
    finally:
        conexion.close()