from collections import deque
from math import ceil
from threading import Lock
from time import monotonic


class LimitadorSolicitudes:
    def __init__(self, maximo, *, ventana=60, reloj=monotonic):
        if maximo < 1 or ventana <= 0:
            raise ValueError("El límite y la ventana deben ser positivos")

        self._maximo = maximo
        self._ventana = ventana
        self._reloj = reloj
        self._intentos = {}
        self._proxima_limpieza = 0.0
        self._lock = Lock()

    def reservar(self, clave):
        """Devuelve (reserva, 0) o (None, segundos de espera)."""
        with self._lock:
            ahora = self._reloj()
            if ahora >= self._proxima_limpieza:
                for clave_guardada, intentos in list(self._intentos.items()):
                    self._quitar_vencidos(intentos, ahora)
                    if not intentos:
                        del self._intentos[clave_guardada]
                self._proxima_limpieza = ahora + self._ventana

            intentos = self._intentos.setdefault(clave, deque())
            self._quitar_vencidos(intentos, ahora)
            if len(intentos) >= self._maximo:
                vence = intentos[0][0] + self._ventana
                return None, max(1, ceil(vence - ahora))

            reserva = (ahora, object())
            intentos.append(reserva)
            return reserva, 0

    def liberar(self, clave, reserva):
        with self._lock:
            intentos = self._intentos.get(clave)
            if intentos is not None and reserva in intentos:
                intentos.remove(reserva)
                if not intentos:
                    del self._intentos[clave]

    def _quitar_vencidos(self, intentos, ahora):
        while intentos and intentos[0][0] + self._ventana <= ahora:
            intentos.popleft()