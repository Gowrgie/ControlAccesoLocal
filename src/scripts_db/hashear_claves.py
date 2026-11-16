"""Admin tool: fills usuarios.clave_hash (Argon2id) from usuarios.clave_acceso.

Run it with a MySQL ADMIN account, not with the restricted user: control_acceso
cannot UPDATE usuarios, on purpose. Only users that still have no hash are
changed, so it can be run again after new users are added.

usuarios.clave_acceso is NOT erased: the button method still compares it.

From the src/ folder:
    python -m scripts_db.hashear_claves --usuario root
"""
import argparse
import getpass

import mysql.connector

from scripts_db.autenticacion import hashear_clave


def hashear_pendientes(conexion):
    """Hashes every user without clave_hash. Returns how many were updated."""
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT id_usuario, clave_acceso FROM usuarios "
        "WHERE clave_hash IS NULL AND clave_acceso IS NOT NULL"
    )
    pendientes = cursor.fetchall()
    for id_usuario, clave in pendientes:
        cursor.execute(
            "UPDATE usuarios SET clave_hash = %s WHERE id_usuario = %s",
            (hashear_clave(clave), id_usuario)
        )
    conexion.commit()
    cursor.close()
    return len(pendientes)


def main():
    parser = argparse.ArgumentParser(description="Fill usuarios.clave_hash with Argon2id hashes.")
    parser.add_argument("--usuario", required=True, help="MySQL admin account (not control_acceso)")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--base", default="control_acceso")
    args = parser.parse_args()

    conexion = mysql.connector.connect(
        host=args.host, user=args.usuario,
        password=getpass.getpass("MySQL password: "), database=args.base
    )
    try:
        print("Users updated:", hashear_pendientes(conexion))
    finally:
        conexion.close()


if __name__ == "__main__":
    main()