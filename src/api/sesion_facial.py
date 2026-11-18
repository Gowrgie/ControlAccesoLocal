"""Reto facial móvil y emisión de la sesión autenticada."""

import json
from base64 import b64decode
from binascii import Error as ErrorBase64
from datetime import timezone
from hashlib import sha256
from secrets import choice, compare_digest, token_urlsafe
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse
from mysql.connector import Error as ErrorMySQL
from starlette.concurrency import run_in_threadpool

from api.rate_limit import LimitadorSolicitudes
from scripts_db import autenticacion

DURACION_RETO = 45
MAX_RETOS = 128
MAX_BYTES_IMAGEN = 256 * 1024
MAX_BYTES_SOLICITUD = 2 * ((MAX_BYTES_IMAGEN + 2) // 3 * 4) + 1024


def _error(codigo, mensaje, headers=None):
    return JSONResponse({"error": mensaje}, status_code=codigo, headers=headers)


def _ip(request):
    return request.client.host if request.client is not None else "desconocida"


async def _leer_json(request, maximo):
    cuerpo = bytearray()
    async for bloque in request.stream():
        if len(cuerpo) + len(bloque) > maximo:
            return _error(413, "La solicitud supera el tamaño permitido")
        cuerpo.extend(bloque)
    try:
        datos = json.loads(cuerpo)
        if isinstance(datos, dict):
            return datos
    except (ValueError, RecursionError):
        pass
    return _error(422, "Datos de solicitud inválidos")


def registrar_sesion_facial(api, verificar_rostro, reloj):
    # Un reto por intento, limitado por IP. El verificador usa un único modelo mutable.
    limite = LimitadorSolicitudes(5, reloj=reloj)
    bloqueo_retos = Lock()
    bloqueo_verificacion = Lock()
    retos = {}

    @api.post("/sessions/face/challenge")
    async def crear_reto(request: Request):
        if verificar_rostro is None:
            return _error(503, "El inicio de sesión facial no está disponible")

        datos = await _leer_json(request, 1024)
        if isinstance(datos, JSONResponse):
            return datos
        huella = datos.get("front_sha256")
        if not isinstance(huella, str) or len(huella) != 64 or any(
            caracter not in "0123456789abcdef" for caracter in huella
        ):
            return _error(422, "Datos de solicitud inválidos")

        ip = _ip(request)
        reserva, espera = limite.reservar(ip)
        if reserva is None:
            return _error(429, "Demasiadas solicitudes", {"Retry-After": str(espera)})

        with bloqueo_retos:
            ahora = reloj()
            for clave, (_, _, vence, _) in list(retos.items()):
                if vence <= ahora:
                    del retos[clave]
            if len(retos) >= MAX_RETOS:
                return _error(503, "El inicio de sesión facial no está disponible")
            clave = token_urlsafe(24)
            direccion = choice(("izquierda", "derecha"))
            retos[clave] = (ip, direccion, ahora + DURACION_RETO, huella)

        return {"challenge_id": clave, "direction": direccion}

    def comprobar_rostro(frontal, inclinada, direccion):
        if not bloqueo_verificacion.acquire(blocking=False):
            return _error(503, "El inicio de sesión facial no está disponible")
        try:
            id_usuario = verificar_rostro(frontal, inclinada, direccion)
            sesion = (
                autenticacion.iniciar_sesion_usuario_verificado(id_usuario)
                if id_usuario is not None else None
            )
        except (ErrorMySQL, RuntimeError):
            return _error(503, "El inicio de sesión facial no está disponible")
        finally:
            bloqueo_verificacion.release()

        if sesion is None:
            return _error(401, "No se pudo verificar el rostro. Intenta de nuevo o usa tu clave.")
        return {
            "token": sesion["token"],
            "expira": sesion["expira"].astimezone(timezone.utc),
        }

    @api.post("/sessions/face")
    async def iniciar_sesion_facial(request: Request):
        if verificar_rostro is None:
            return _error(503, "El inicio de sesión facial no está disponible")

        datos = await _leer_json(request, MAX_BYTES_SOLICITUD)
        if isinstance(datos, JSONResponse):
            return datos
        clave = datos.get("challenge_id")
        if not isinstance(clave, str) or len(clave) != 32:
            return _error(422, "Datos de solicitud inválidos")

        with bloqueo_retos:
            reto = retos.get(clave)
            if reto is None or reto[0] != _ip(request):
                return _error(401, "El reto facial no es válido o ya venció")
            del retos[clave]

        _, direccion, vence, huella = reto
        if vence <= reloj():
            return _error(401, "El reto facial no es válido o ya venció")

        try:
            frontal = b64decode(datos["front_image"], validate=True)
            inclinada = b64decode(datos["tilted_image"], validate=True)
        except (ErrorBase64, ValueError, KeyError, TypeError):
            return _error(422, "Datos de solicitud inválidos")

        if not frontal or not inclinada or frontal == inclinada:
            return _error(422, "Se necesitan dos capturas distintas")
        if max(len(frontal), len(inclinada)) > MAX_BYTES_IMAGEN:
            return _error(413, "Las capturas superan el tamaño permitido")

        if not compare_digest(sha256(frontal).hexdigest(), huella):
            return _error(401, "La captura no corresponde al reto facial")

        return await run_in_threadpool(comprobar_rostro, frontal, inclinada, direccion)
