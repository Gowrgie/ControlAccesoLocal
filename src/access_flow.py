"""Access flow module: the capture and validation flow shared by both modes.

ControlAcceso is the base class of InterfazControlAcceso (gui.py) and
ModoBotones (headless_mode.py). It coordinates hardware.py and
access_logic.py, and owns the capture state (method, phase, identifier,
password, timers). It knows nothing about screens: whatever must be shown is
delegated to the hooks below, which each mode implements.

Hooks that a subclass must provide:
    mostrar_standby()                       return to the waiting state
    mostrar_resultado(resultado, accionar)  show/print the result
    anunciar_sistema_listo()                system ready announcement
Optional hook:
    notificar_error_hardware(error)         default: do nothing

Requirements for the object that uses this class:
    self.root must offer after(ms, fn), after_cancel(token) and destroy()
    (a Tk root or headless_mode.TemporizadorFisico).
"""
import time

from access_logic import validar_acceso_por_botones, validar_acceso_por_rostro
from hardware import ControlHardware, PINES_BOTONES


class ControlAcceso:

    def preparar_estado(self):
        # Used with a window and in physical mode: both share the same rules
        # for capture, presence, exclusion and cleanup.
        self.hardware = ControlHardware(self.programar_accion)
        self._cerrando = False
        # None: both methods available. A chosen method reserves the attempt.
        self._captura_metodo = None
        self._captura_fase = "identificador"
        self._captura_id = ""
        self._captura_clave = ""
        self._ultima_pulsacion = 0.0
        self._en_resultado = False
        self._hardware_after = None
        self._pir_after = None
        # Keeping the timers lets them be cancelled when the app closes.
        self._acciones_after = set()

    @property
    def pir_activo(self):
        return self.hardware.pir.activo

    # ============ hooks ============
    def mostrar_standby(self):
        raise NotImplementedError

    def mostrar_resultado(self, resultado, accionar=True):
        raise NotImplementedError

    def anunciar_sistema_listo(self):
        raise NotImplementedError

    def notificar_error_hardware(self, error):
        pass

    # ============ closing ============
    def on_closing(self):
        if self._cerrando:
            return

        self._cerrando = True

        cerrar_facial = getattr(self, "cerrar_reconocimiento_facial", None)
        if callable(cerrar_facial):
            try:
                cerrar_facial()
            except Exception as error:
                print(
                    f"[FACIAL] Error al cerrar la ventana: {error}",
                    flush=True,
                )

        for token in [
            self._pir_after,
            self._hardware_after,
            *self._acciones_after,
        ]:
            if token:
                try:
                    self.root.after_cancel(token)
                except Exception:
                    pass

        self.hardware.cerrar_hardware()
        self.hardware.limpiar_lock()
        self.root.destroy()

    # ============ timers and state ============
    def programar_accion(self, milisegundos, funcion):
        # Schedules an action without sleeping the main loop.
        def ejecutar():
            self._acciones_after.discard(token)
            if not self._cerrando:
                funcion()
        token = self.root.after(milisegundos, ejecutar)
        self._acciones_after.add(token)

    def reiniciar_estado_espera(self):
        # Common part of every return to the waiting state.
        if self._en_resultado:
            self.hardware.servo_reposo()
        self._en_resultado = False
        self._captura_metodo = None
        self._captura_id = ""
        self._captura_clave = ""
        self.hardware.pir.reiniciar()
        self.hardware.botones.reiniciar()

    def actualizar_presencia(self, ahora):
        # monotonic measures intervals without depending on system clock changes.
        ocupado = self._en_resultado or self._captura_metodo is not None
        self.hardware.pir.actualizar(ahora, ocupado, self.anunciar_sistema_listo)
        self.intentar_inicio_facial()

    def intentar_inicio_facial(self):
        """Inicia el reconocedor al habilitarse la presencia del PIR."""
        if (
            self._cerrando
            or self._en_resultado
            or self._captura_metodo is not None
            or not self.pir_activo
            or not getattr(self, "puede_facial", False)
        ):
            return

        abrir = getattr(self, "iniciar_reconocimiento_facial", None)
        if not callable(abrir):
            self.puede_facial = False
            print("[FACIAL] La interfaz no tiene el método para abrir el reconocedor.", flush=True)
            return

        # Reserva el intento para que botones y pantalla no lo ocupen.
        self._captura_metodo = "facial"
        print("[MÉTODO] Iniciando reconocimiento facial.", flush=True)

        try:
            abrir()
        except Exception as error:
            fallo = getattr(self, "fallo_facial", None)
            if callable(fallo):
                fallo(str(error))
            else:
                self._captura_metodo = None
                self.puede_facial = False
                print(f"[FACIAL] No se pudo abrir el reconocedor: {error}", flush=True)

    # ============ button capture ============
    def cancelar_captura_fisica(self):
        print("[CANCELADO] 4 segundos sin pulsación. Identificador y clave descartados.", flush=True)
        self.hardware.senal_captura_cancelada()
        self.mostrar_standby()

    def leer_botones(self):
        if self._cerrando:
            return
        try:
            ahora = time.monotonic()
            self.actualizar_presencia(ahora)
            bajos = self.hardware.botones.leer_bajos()
            pin = self.hardware.botones.detectar_pulsacion(bajos, ahora)
            # This deadline starts with the first accepted press and is renewed
            # with each digit; it is independent from the 4 s of retained presence.
            vencio = (self._captura_metodo == "botones" and not self._en_resultado
                      and ahora - self._ultima_pulsacion >= 4)
            if vencio:
                # Rule kept from the physical program: a 4 or 5 digit password is
                # sent when the deadline expires; with 6 it is sent immediately.
                # An incomplete identifier or a password under 4 is discarded.
                if self._captura_fase == "clave" and len(self._captura_clave) >= 4:
                    self.validar_botones()
                else:
                    self.cancelar_captura_fisica()
            elif pin is not None:
                if self._en_resultado:
                    print("[IGNORADO] Mostrando resultado.", flush=True)
                elif self._captura_metodo == "interfaz_grafica":
                    print("[IGNORADO] La pantalla está atendiendo este intento.", flush=True)
                elif self._captura_metodo == "facial":
                    print("[IGNORADO] El reconocimiento facial está atendiendo este intento.", flush=True)
                elif self._captura_metodo is None and not self.pir_activo:
                    print("[IGNORADO] Sin presencia habilitada. Espere la estabilización y acérquese al PIR.", flush=True)
                else:
                    if self._captura_metodo is None:
                        self._captura_metodo = "botones"
                        self._captura_fase = "identificador"
                        self._captura_id = self._captura_clave = ""
                        print("[MÉTODO] Botones. Capture 4 dígitos de identificador.", flush=True)
                    self.agregar_boton(PINES_BOTONES[pin], ahora)
        except Exception as error:
            print("Error en hardware:", error)
            self.notificar_error_hardware(error)
            self.on_closing()
            return
        # Polling about every 20 ms; the synchronous MySQL query can delay it
        # during validation, when no more digits are accepted anyway.
        self._hardware_after = self.root.after(20, self.leer_botones)

    def agregar_boton(self, valor, ahora):
        print(f"[ACEPTADO] Pulsación; campo: {self._captura_fase}", flush=True)
        self._ultima_pulsacion = ahora
        self.hardware.tono_buzzer(.04)
        if self._captura_fase == "identificador":
            self._captura_id += valor
            print(f"[IDENTIFICADOR] {self._captura_id} ({len(self._captura_id)}/4)", flush=True)
            # The phase changes after saving the fourth digit: that same button
            # is NOT reused as the first digit of the password.
            if len(self._captura_id) == 4:
                self._captura_fase = "clave"
                print("[CLAVE] Identificador completo. La SIGUIENTE pulsación inicia la clave.", flush=True)
        else:
            self._captura_clave += valor
            print("Dígitos de clave capturados:", len(self._captura_clave))
            if len(self._captura_clave) == 6:
                self.validar_botones()

    def validar_botones(self):
        self.identificador = self._captura_id
        resultado = validar_acceso_por_botones(self._captura_id, self._captura_clave)
        self._captura_id = self._captura_clave = ""
        self.mostrar_resultado(resultado)

    # ============ facial identification ============
    def procesar_identificacion_facial(self, id_usuario):
        """Procesa el usuario identificado y muestra el resultado de acceso."""
        if self._en_resultado or self._captura_metodo not in (None, "facial"):
            print("[IGNORADO] Hay otra operación en curso.", flush=True)
            return False

        if self._captura_metodo is None and not self.pir_activo:
            print("[IGNORADO] Sin presencia habilitada.", flush=True)
            return False

        self._captura_metodo = "facial"
        self.identificador = ""

        if id_usuario is not None:
            try:
                from scripts_db.db_conexion import obtener_permisos_por_usuario

                usuario = obtener_permisos_por_usuario(id_usuario)
                self.identificador = (
                    usuario.get("nombre") if usuario else None
                ) or f"Usuario {id_usuario}"
            except Exception as error:
                print(f"[FACIAL] No se pudo consultar el nombre: {error}", flush=True)
                self.identificador = f"Usuario {id_usuario}"

        print("[MÉTODO] Rostro.", flush=True)
        resultado = validar_acceso_por_rostro(id_usuario)
        self.mostrar_resultado(resultado)
        return True