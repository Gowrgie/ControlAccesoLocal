"""Headless mode module: physical operation without a window (SSH).

ModoBotones reuses the whole capture flow from access_flow.ControlAcceso and
replaces the screens with console messages. TemporizadorFisico replaces only
after/after_cancel/mainloop of Tk, so no desktop is needed. It does not
simulate an interface or the GPIO.

Public interface:
    TemporizadorFisico()   after(ms, fn), after_cancel(token), destroy(), mainloop()
    ModoBotones(root)      root: a TemporizadorFisico
"""
import heapq
import itertools
import time

from access_flow import ControlAcceso


class TemporizadorFisico:
    """Timers without Tk: physical mode does not need a desktop."""

    def __init__(self):
        self._cola = []
        self._ids = itertools.count()
        self._pendientes = set()
        self.activo = True

    def after(self, ms, funcion):
        token = next(self._ids) + 1
        self._pendientes.add(token)
        heapq.heappush(self._cola, (time.monotonic() + ms / 1000, token, funcion))
        return token

    def after_cancel(self, token):
        # Deferred cancellation: the item stays in the queue, but mainloop
        # skips it when its turn comes if it is no longer in _pendientes.
        self._pendientes.discard(token)

    def destroy(self):
        self.activo = False
        self._cola.clear()
        self._pendientes.clear()

    def mainloop(self):
        while self.activo:
            ahora = time.monotonic()
            while self._cola and self._cola[0][0] <= ahora and self.activo:
                _, token, funcion = heapq.heappop(self._cola)
                if token in self._pendientes:
                    self._pendientes.remove(token)
                    funcion()
                ahora = time.monotonic()
            time.sleep(.005)


class ModoBotones(ControlAcceso):
    """Reuses the capture and the hardware without building any window."""

    def __init__(self, root):
        self.root = root
        self.preparar_estado()
        self.hardware.crear_lock()
        self.hardware.configurar_gpio()
        self.hardware.inicializar_hardware()
        self.identificador = ""
        self.mostrar_standby()
        self.leer_botones()

    def anunciar_sistema_listo(self):
        self.hardware.tono_buzzer(.15)
        print("[LISTO] Acceso físico habilitado.", flush=True)

    def mostrar_standby(self):
        self.reiniciar_estado_espera()
        self._captura_fase = "identificador"
        print("[SOLO BOTONES] Esperando sensor. Identificador: 4 pulsaciones; clave: 4 a 6.", flush=True)

    def mostrar_resultado(self, resultado, accionar=True):
        self._en_resultado = True
        mensajes = {
            "autorizado": "ACCESO AUTORIZADO",
            "sin_permiso": "ACCESO DENEGADO: usuario sin permiso",
            "no_reconocido": "ACCESO RECHAZADO: datos incorrectos",
            "error_sistema": "ERROR DEL SISTEMA: no se pudo validar",
        }
        print(mensajes.get(resultado, mensajes["error_sistema"]), flush=True)
        if accionar:
            self.hardware.respuesta_hardware(resultado)
        self.programar_accion(4000, self.mostrar_standby)