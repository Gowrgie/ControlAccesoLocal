"""One-use challenges signed by a key previously linked to an account."""

from base64 import b64decode
from datetime import timezone
from secrets import token_urlsafe
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse
from mysql.connector import Error as ErrorMySQL
from pydantic import BaseModel, Field

from api.rate_limit import LimitadorSolicitudes
from scripts_db import autenticacion

PATRON_ID = r"^[A-Za-z0-9_-]{32}$"
DURACION_RETO = 60
MAX_RETOS = 128


class RetoBiometricoRequest(BaseModel):
    credential_id: str = Field(pattern=PATRON_ID, min_length=32, max_length=32)


class FirmaBiometricaRequest(BaseModel):
    challenge: str = Field(pattern=PATRON_ID, min_length=32, max_length=32)
    signature: str = Field(min_length=1, max_length=108)


def _error(codigo, mensaje, headers=None):
    return JSONResponse({"error": mensaje}, status_code=codigo, headers=headers)


def _ip(request):
    return request.client.host if request.client is not None else "desconocida"


def registrar_sesion_biometrica(api, reloj):
    limite = LimitadorSolicitudes(5, reloj=reloj)
    retos = {}
    bloqueo = Lock()

    @api.post("/sessions/biometric/challenge")
    def crear_reto(datos: RetoBiometricoRequest, request: Request):
        ip = _ip(request)
        reserva, espera = limite.reservar(ip)
        if reserva is None:
            return _error(429, "Demasiadas solicitudes", {"Retry-After": str(espera)})

        with bloqueo:
            ahora = reloj()
            for clave, (_, _, vence) in list(retos.items()):
                if vence <= ahora:
                    del retos[clave]
            if len(retos) >= MAX_RETOS:
                return _error(503, "El inicio biométrico no está disponible")
            reto = token_urlsafe(24)
            retos[reto] = (datos.credential_id, ip, ahora + DURACION_RETO)
        return {"challenge": reto}

    @api.post("/sessions/biometric")
    def iniciar_sesion_biometrica(datos: FirmaBiometricaRequest, request: Request):
        with bloqueo:
            reto = retos.get(datos.challenge)
            if reto is None or reto[1] != _ip(request):
                return _error(401, "El reto biométrico no es válido o ya venció")
            del retos[datos.challenge]
        id_credencial, _, vence = reto
        if vence <= reloj():
            return _error(401, "El reto biométrico no es válido o ya venció")
        try:
            firma = b64decode(datos.signature, validate=True)
        except ValueError:
            return _error(422, "Firma biométrica inválida")
        try:
            sesion = autenticacion.iniciar_sesion_biometrica(
                id_credencial, datos.challenge.encode("ascii"), firma
            )
        except (ErrorMySQL, ImportError):
            return _error(503, "El inicio biométrico no está disponible")
        if sesion is None:
            return _error(401, "No se pudo verificar la credencial biométrica")
        return {"token": sesion["token"], "expira": sesion["expira"].astimezone(timezone.utc)}
