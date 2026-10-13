"""Access logic module: decides whether an access attempt is authorized.

It only depends on scripts_db.db_conexion, so it can be imported on any
machine (no GPIO, no Tkinter). Both authentication paths (screen and
buttons) end here, and both return one of these results:

    "autorizado", "sin_permiso", "no_reconocido", "error_sistema"

Public interface:
    normalizar_rol(nombre) -> str
    validar_acceso_por_rol(identificador, clave, rol_seleccionado) -> str
        Screen path: checks the role chosen on screen and logs "interfaz_grafica".
    validar_acceso_por_botones(identificador, clave) -> str
        Button path: db_conexion validates and logs "botones".
"""
import unicodedata

try:
    from scripts_db.db_conexion import validar_acceso, buscar_usuario, registrar_intento
except ImportError:
    print("Error: No se pudo importar db_conexion. No se autorizarán accesos.")
    validar_acceso = buscar_usuario = registrar_intento = None


def normalizar_rol(nombre):
    # Allows comparing "Servicio técnico" and "servicio_tecnico" without
    # differences in accents, case or separators.
    texto = unicodedata.normalize("NFKD", str(nombre or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.lower().replace("_", " ").split())


def validar_acceso_por_rol(identificador, clave, rol_seleccionado):
    """Uses the existing DB functions and logs a single final decision."""
    if buscar_usuario is None or registrar_intento is None:
        return "error_sistema"
    try:
        usuario = buscar_usuario(identificador, clave)
        id_usuario = None
        if usuario is None:
            resultado = "no_reconocido"
        else:
            id_usuario = usuario["id_usuario"]
            rol_real = normalizar_rol(usuario["nombre_rol"])
            rol_pedido = {"general": "usuario general", "technical": "servicio tecnico",
                          "admin": "administrador"}.get(rol_seleccionado)
            # The administrator can choose any role but also needs opening
            # permission. Everyone else can only choose their own role.
            es_admin = (rol_real == "administrador" and bool(usuario["permiso_administracion"]))
            if not usuario["permiso_apertura"] or rol_pedido is None:
                resultado = "sin_permiso"
            elif es_admin or (rol_real == rol_pedido and rol_pedido != "administrador"):
                resultado = "autorizado"
            else:
                resultado = "sin_permiso"
        # The attempt is logged after checking the role so an authorization
        # that should be rejected is never stored. validar_acceso is not called
        # here: it also logs, which would duplicate the attempt.
        registrar_intento(id_usuario, "interfaz_grafica", resultado)
        return resultado
    except Exception as error:
        print("Error al validar usuario y rol:", error, flush=True)
        return "error_sistema"


def validar_acceso_por_botones(identificador, clave):
    """Button path: there is no role chosen on screen, so the original DB
    function validates the credentials and the opening permission and logs
    the attempt with the "botones" mechanism."""
    try:
        return (validar_acceso(identificador, clave, "botones")
                if validar_acceso is not None else "error_sistema")
    except Exception as error:
        print("Error al validar botones:", error)
        return "error_sistema"