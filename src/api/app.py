from datetime import datetime, timezone
from hashlib import sha256
from time import monotonic
from typing import Optional
from uuid import UUID
from fastapi.exceptions import RequestValidationError

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from mysql.connector import Error as ErrorMySQL
from pydantic import BaseModel, Field, SecretStr

from api.rate_limit import LimitadorSolicitudes
from api.sesion_biometrica import registrar_sesion_biometrica
from scripts_db import autenticacion


class LoginRequest(BaseModel):
    identificador: str
    clave: SecretStr
    biometric_public_key: Optional[str] = Field(default=None, min_length=1, max_length=164)


class Session(BaseModel):
    token: str
    expira: datetime
    biometric_credential_id: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str


class PresenceResponse(BaseModel):
    present: bool


class AccessRequestCreate(BaseModel):
    request_id: UUID


class AccessRequestStatus(BaseModel):
    request_id: str
    state: str
    result: Optional[str] = None


def crear_api(
    *,
    obtener_presencia=None,
    despachador=None,
    reloj=monotonic,
    limite_login_ip=10,
    limite_login_identificador=5,
    limite_aperturas_usuario=10,
    limite_consultas_sesion=120,
):
    api = FastAPI(title="ControlAccesoLocal Mobile API", version="1.0")

    @api.exception_handler(RequestValidationError)
    async def manejar_solicitud_invalida(
        _request: Request, _error: RequestValidationError
    ):
        return JSONResponse(
            status_code=422,
            content={"error": "Datos de solicitud inválidos"},
        )

    registrar_sesion_biometrica(api, reloj)

    bearer = HTTPBearer(auto_error=False)

    login_por_ip = LimitadorSolicitudes(limite_login_ip, reloj=reloj)
    login_por_identificador = LimitadorSolicitudes(
        limite_login_identificador, reloj=reloj
    )

    aperturas_por_usuario = LimitadorSolicitudes(
        limite_aperturas_usuario, reloj=reloj
    )
    consultas_por_sesion = LimitadorSolicitudes(
        limite_consultas_sesion, reloj=reloj
    )

    def demasiadas_solicitudes(espera):
        return JSONResponse(
            status_code=429,
            content={"error": "Demasiadas solicitudes"},
            headers={"Retry-After": str(espera)},
        )

    @api.post(
        "/sessions",
        response_model=Session,
        response_model_exclude_none=True,
        responses={
            401: {"model": ErrorResponse},
            429: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def iniciar_sesion(datos: LoginRequest, request: Request):
        ip = request.client.host if request.client is not None else "desconocida"
        identificador = datos.identificador.strip().casefold()

        reserva_ip, espera = login_por_ip.reservar(ip)
        if reserva_ip is None:
            return demasiadas_solicitudes(espera)

        reserva_usuario, espera = login_por_identificador.reservar(identificador)
        if reserva_usuario is None:
            login_por_ip.liberar(ip, reserva_ip)
            return demasiadas_solicitudes(espera)

        credenciales_invalidas = False
        try:
            argumentos = {}
            if datos.biometric_public_key is not None:
                from scripts_db.claves_dispositivo import decodificar_clave_publica

                try:
                    argumentos["clave_publica"] = decodificar_clave_publica(datos.biometric_public_key)
                except ValueError:
                    return JSONResponse(
                        status_code=422, content={"error": "Clave pública biométrica inválida"},
                    )
            sesion = autenticacion.iniciar_sesion(
                datos.identificador, datos.clave.get_secret_value(), **argumentos
            )
            credenciales_invalidas = sesion is None
        except (ErrorMySQL, ImportError):
            return JSONResponse(
                status_code=503,
                content={"error": "Servicio de autenticación no disponible"},
            )
        finally:
            if not credenciales_invalidas:
                login_por_identificador.liberar(identificador, reserva_usuario)

        if credenciales_invalidas:
            return JSONResponse(
                status_code=401,
                content={"error": "Credenciales inválidas"},
            )

        return Session(
            token=sesion["token"],
            expira=sesion["expira"].astimezone(timezone.utc),
            biometric_credential_id=sesion.get("biometric_credential_id"),
        )

    @api.delete(
        "/sessions",
        status_code=204,
        response_class=Response,
        responses={
            401: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def cerrar_sesion(
        credencial: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    ):
        if credencial is None or not credencial.credentials.strip():
            return JSONResponse(
                status_code=401,
                content={"error": "Se requiere un token Bearer"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            autenticacion.cerrar_sesion(credencial.credentials)
        except ErrorMySQL:
            return JSONResponse(
                status_code=503,
                content={"error": "Servicio de autenticación no disponible"},
            )

        return Response(status_code=204)

    @api.get(
        "/presence",
        response_model=PresenceResponse,
        responses={
            401: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def consultar_presencia(
        credencial: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    ):
        try:
            usuario_id = (
                autenticacion.validar_sesion(credencial.credentials)
                if credencial is not None
                else None
            )
        except ErrorMySQL:
            return JSONResponse(
                status_code=503,
                content={"error": "Servicio de autenticación no disponible"},
            )

        if usuario_id is None:
            return JSONResponse(
                status_code=401,
                content={"error": "Sesión inválida o vencida"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        sesion_id = sha256(credencial.credentials.encode("utf-8")).hexdigest()
        reserva, espera = consultas_por_sesion.reservar(sesion_id)
        if reserva is None:
            return demasiadas_solicitudes(espera)

        presente = obtener_presencia() if obtener_presencia is not None else None
        if presente is None:
            return JSONResponse(
                status_code=503,
                content={"error": "Sensor de presencia no disponible"},
            )

        return PresenceResponse(present=presente)

    @api.post(
        "/access-requests",
        status_code=202,
        response_model=AccessRequestStatus,
        responses={
            401: {"model": ErrorResponse},
            403: {"model": ErrorResponse},
            409: {"model": AccessRequestStatus},
            503: {"model": ErrorResponse},
        },
    )
    def solicitar_acceso(
        datos: AccessRequestCreate,
        credencial: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    ):
        token = credencial.credentials if credencial is not None else None

        try:
            usuario_id = autenticacion.validar_sesion(token) if token else None
        except ErrorMySQL:
            return JSONResponse(
                status_code=503,
                content={"error": "Servicio de autenticación no disponible"},
            )

        if usuario_id is None:
            return JSONResponse(
                status_code=401,
                content={"error": "Sesión inválida o vencida"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        reserva, espera = aperturas_por_usuario.reservar(usuario_id)
        if reserva is None:
            return demasiadas_solicitudes(espera)

        if despachador is None:
            return JSONResponse(
                status_code=503,
                content={"error": "Controlador no disponible"},
            )

        request_id = str(datos.request_id)
        sesion_id = sha256(token.encode("utf-8")).hexdigest()

        try:
            estado = despachador.consultar(request_id, sesion_id)
            if estado is not None:
                return JSONResponse(status_code=409, content=estado)

            presente = obtener_presencia() if obtener_presencia is not None else None
            if presente is None:
                return JSONResponse(
                    status_code=503,
                    content={"error": "Sensor de presencia no disponible"},
                )
            if not presente:
                return JSONResponse(
                    status_code=403,
                    content={"error": "No hay presencia activa"},
                )

            creada = despachador.enviar(request_id, sesion_id, usuario_id)
            estado = despachador.consultar(request_id, sesion_id)
        except PermissionError:
            return JSONResponse(
                status_code=403,
                content={"error": "La solicitud pertenece a otra sesión"},
            )

        if not creada:
            return JSONResponse(status_code=409, content=estado)

        return estado

    @api.get(
        "/access-requests/{request_id}",
        response_model=AccessRequestStatus,
        responses={
            401: {"model": ErrorResponse},
            403: {"model": ErrorResponse},
            404: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def consultar_solicitud(
        request_id: UUID,
        credencial: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    ):
        token = credencial.credentials if credencial is not None else None

        try:
            usuario_id = autenticacion.validar_sesion(token) if token else None
        except ErrorMySQL:
            return JSONResponse(
                status_code=503,
                content={"error": "Servicio de autenticación no disponible"},
            )

        if usuario_id is None:
            return JSONResponse(
                status_code=401,
                content={"error": "Sesión inválida o vencida"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        sesion_id = sha256(token.encode("utf-8")).hexdigest()

        reserva, espera = consultas_por_sesion.reservar(sesion_id)
        if reserva is None:
            return demasiadas_solicitudes(espera)

        if despachador is None:
            return JSONResponse(
                status_code=503,
                content={"error": "Controlador no disponible"},
            )


        try:
            estado = despachador.consultar(str(request_id), sesion_id)
        except PermissionError:
            return JSONResponse(
                status_code=403,
                content={"error": "La solicitud pertenece a otra sesión"},
            )

        if estado is None:
            return JSONResponse(
                status_code=404,
                content={"error": "Solicitud no encontrada"},
            )

        return estado

    return api