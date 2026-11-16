from collections import deque
from dataclasses import dataclass
from threading import Lock
from time import monotonic
from uuid import UUID


@dataclass(frozen=True)
class SolicitudAcceso:
    request_id: str
    sesion_id: str
    usuario_id: int
    vence_en: float


class DespachadorAcceso:
    def __init__(self, *, reloj=monotonic):
        self._cola = deque()
        self._solicitudes = {}
        self._lock = Lock()
        self._en_ejecucion = None
        self._resultados = {}
        self._controlador_ocupado = False
        self._reloj = reloj
        self._vencidas = set()

    def enviar(self, request_id: str, sesion_id: str, usuario_id: int) -> bool:
        """Encola una solicitud nueva. Devuelve False si la sesión la repite."""
        request_id = str(UUID(request_id))

        with self._lock:
            existente = self._solicitudes.get(request_id)
            if existente is not None:
                if existente.sesion_id != sesion_id:
                    raise PermissionError("La solicitud pertenece a otra sesión")
                return False

            solicitud = SolicitudAcceso(
                request_id, sesion_id, usuario_id, self._reloj() + 10.0
            )
            self._solicitudes[request_id] = solicitud
            self._cola.append(solicitud)
            return True

    def tomar(self, *, controlador_ocupado: bool):
        """Reserva el turno para la solicitud más antigua de la cola."""
        with self._lock:
            self._controlador_ocupado = controlador_ocupado
            self._vencer_cola()

            if controlador_ocupado or self._en_ejecucion is not None:
                return None
            if not self._cola:
                return None

            self._en_ejecucion = self._cola.popleft()
            return self._en_ejecucion

    def completar(self, request_id: str, resultado: str) -> None:
        """Guarda el resultado de la solicitud activa y libera su turno."""
        request_id = str(UUID(request_id))

        with self._lock:
            activa = self._en_ejecucion
            if activa is None or activa.request_id != request_id:
                raise ValueError("La solicitud no tiene el turno del controlador")

            self._resultados[request_id] = resultado
            self._en_ejecucion = None

    def consultar(self, request_id: str, sesion_id: str):
        """Devuelve el estado de la solicitud a la sesión que la creó."""
        request_id = str(UUID(request_id))

        with self._lock:
            solicitud = self._solicitudes.get(request_id)
            if solicitud is None:
                return None
            if solicitud.sesion_id != sesion_id:
                raise PermissionError("La solicitud pertenece a otra sesión")

            self._vencer_cola()
            resultado = None

            if request_id in self._vencidas:
                estado = "expired"
            elif request_id in self._resultados:
                estado = "complete"
                resultado = self._resultados[request_id]
            elif self._en_ejecucion == solicitud:
                estado = "pending"
            elif (
                self._controlador_ocupado
                or self._en_ejecucion is not None
                or self._cola[0] != solicitud
            ):
                estado = "busy"
            else:
                estado = "pending"

            return {"request_id": request_id, "state": estado, "result": resultado}

    def _vencer_cola(self):
        """Retira las solicitudes vencidas mientras el dispatcher tiene el lock."""
        ahora = self._reloj()
        while self._cola and self._cola[0].vence_en <= ahora:
            solicitud = self._cola.popleft()
            self._vencidas.add(solicitud.request_id)