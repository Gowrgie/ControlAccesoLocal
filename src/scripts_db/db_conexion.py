import mysql.connector
from datetime import datetime

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "tu_password"
DB_NAME = "control_acceso"

TIEMPO_MAXIMO_CONEXION = 2 


def conectar_bd():
    conexion = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        connection_timeout=TIEMPO_MAXIMO_CONEXION
    )
    return conexion


def buscar_usuario(identificador_ingresado, clave_ingresada):
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True) 
    query = """
        SELECT usuarios.id_usuario, usuarios.nombre, roles.nombre_rol,
               roles.permiso_apertura, roles.permiso_administracion
        FROM usuarios
        JOIN roles ON usuarios.id_rol = roles.id_rol
        WHERE usuarios.identificador = %s AND usuarios.clave_acceso = %s
    """
    cursor.execute(query, (identificador_ingresado, clave_ingresada))
    usuario = cursor.fetchone() 

    cursor.close()
    conexion.close()

    return usuario


def registrar_intento(id_usuario, mecanismo, resultado):
    conexion = conectar_bd()
    cursor = conexion.cursor()

    query = """
        INSERT INTO intentos_acceso (id_usuario, fecha_hora, mecanismo, resultado)
        VALUES (%s, %s, %s, %s)
    """
    ahora = datetime.now()
    cursor.execute(query, (id_usuario, ahora, mecanismo, resultado))

    conexion.commit() 
    cursor.close()
    conexion.close()


def validar_acceso(identificador_ingresado, clave_ingresada, mecanismo):
    try:
        usuario = buscar_usuario(identificador_ingresado, clave_ingresada)

        if usuario is None:
            print("Usuario no reconocido")
            registrar_intento(None, mecanismo, "no_reconocido")
            return "no_reconocido"

        if usuario["permiso_apertura"] == 0:
            print("Usuario reconocido pero sin permiso:", usuario["nombre"])
            registrar_intento(usuario["id_usuario"], mecanismo, "sin_permiso")
            return "sin_permiso"
        print("Acceso autorizado para:", usuario["nombre"])
        registrar_intento(usuario["id_usuario"], mecanismo, "autorizado")
        return "autorizado"
    except mysql.connector.Error as error:
        print("Error al consultar la base de datos:", error)
        return "error_sistema"