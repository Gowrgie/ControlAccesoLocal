"""Hardware module: every direct access to GPIO, lgpio and the process lock.

Nothing outside this module imports RPi.GPIO or lgpio.

Pin map (BCM numbering, not the physical header position):
    buttons 1/2/3 -> GPIO 14/15/18 (pull-up: pressed = LOW)
    PIR sensor    -> GPIO 27
    green LED     -> GPIO 23, red LED -> GPIO 24, buzzer -> GPIO 25
    servo         -> GPIO 26 (driven through lgpio)

Public interface:
    ControlHardware(programar_accion)
        programar_accion(ms, funcion) is supplied by the caller and schedules
        timed outputs (LED off, buzzer off, servo back to rest).
        .pir        SensorPIR      presence detection and stabilization
        .botones    LectorBotones  debounced button reading
        .crear_lock() / .limpiar_lock()
        .configurar_gpio() / .inicializar_hardware()
        .tono_buzzer(duracion)
        .respuesta_hardware(resultado)    LED + servo + buzzer for a result
        .senal_captura_cancelada()        signal for a discarded capture
        .servo_reposo()
        .cerrar_hardware()                safe to call more than once
"""
import fcntl
import time

import lgpio
import RPi.GPIO as GPIO

LOCK_FILE = "/tmp/control_acceso.lock"
LOCK_IDENTIFIER = "interfaz_grafica"

PIR_PIN = 27
PINES_BOTONES = {14: "1", 15: "2", 18: "3"}
LED_VERDE = 23
LED_ROJO = 24
BUZZER = 25
SERVO = 26

# Approximate SG90 pulse widths: 1000 us = reject (0 deg),
# 1500 us = rest (90 deg), 2000 us = open (180 deg).
SERVO_RECHAZO = 1000
SERVO_REPOSO = 1500
SERVO_APERTURA = 2000

TIEMPO_ESTABILIZACION_PIR = 30   # seconds before the PIR is trusted
VENTANA_PRESENCIA = 4.0          # seconds that presence is kept after the PIR drops


class SensorPIR:
    """PIR presence detection with the 30 s stabilization and the 4 s window.

    actualizar() keeps .activo up to date. The sensor never authorizes access:
    it only enables the interaction.
    """

    def __init__(self):
        self.activo = False
        self._diagnostico = None
        # Retained-presence deadline; not the timer between button presses.
        self._presencia_hasta = 0.0
        self._inicio = time.monotonic()
        self._armado = False
        self._inicio_listo = False

    def reiniciar(self):
        """Back to waiting: the sensor must be seen at rest again."""
        self._armado = False
        self._presencia_hasta = 0.0
        self.activo = False

    def actualizar(self, ahora, ocupado, al_estar_listo):
        """ahora: time.monotonic() value. ocupado: True while a capture or a
        result is in progress. al_estar_listo: called once, when the sensor is
        stabilized and at rest for the first time."""
        presencia = GPIO.input(PIR_PIN) == GPIO.HIGH
        if presencia != self._diagnostico:
            print("[PIR]", "PRESENCIA (HIGH)" if presencia else "REPOSO (LOW)", flush=True)
            self._diagnostico = presencia
        if ocupado:
            # A capture already started does not depend on the PIR staying active.
            return
        # Do not enable capture until 30 s have passed AND the PIR was seen LOW.
        if ahora - self._inicio < TIEMPO_ESTABILIZACION_PIR:
            self.activo = False
            return
        if not presencia and not self._armado:
            self._armado = True
            print("[LISTO] Sensor estabilizado y en reposo. Esperando presencia.", flush=True)
            if not self._inicio_listo:
                self._inicio_listo = True
                al_estar_listo()
        # While the PIR is HIGH the window is renewed. After it returns to LOW,
        # 4 s remain to start by screen or buttons.
        if presencia and self._armado:
            self._presencia_hasta = ahora + VENTANA_PRESENCIA
        activo = ahora < self._presencia_hasta
        if activo != self.activo:
            print("[PRESENCIA]", "Habilitada para pantalla y botones" if activo
                  else "Ventana de 4 segundos terminada", flush=True)
        self.activo = activo


class LectorBotones:
    """Reads the three buttons with 30 ms debounce on press and release."""

    def __init__(self):
        self._anteriores = set()
        self._crudo = None
        self._cambio = 0.0
        self._estable = None
        self._esperar_liberacion = True

    def reiniciar(self):
        """Back to waiting: a held button must be released before counting."""
        self._esperar_liberacion = True

    def leer_bajos(self):
        """Set of GPIO pins whose button is currently pressed (LOW)."""
        return {pin for pin in PINES_BOTONES if GPIO.input(pin) == GPIO.LOW}

    def detectar_pulsacion(self, bajos, ahora):
        """Returns the GPIO pin of a new accepted press, or None.

        A held button counts once. Two buttons together are ignored until
        all of them are released.
        """
        for pin in sorted(bajos - self._anteriores):
            print(f"[BOTÓN {PINES_BOTONES[pin]} / GPIO {pin}] PRESIONADO (LOW)", flush=True)
        for pin in sorted(self._anteriores - bajos):
            print(f"[BOTÓN {PINES_BOTONES[pin]} / GPIO {pin}] LIBERADO (HIGH)", flush=True)
        self._anteriores = set(bajos)
        crudo = next(iter(bajos)) if len(bajos) == 1 else ("varios" if bajos else None)
        if crudo != self._crudo:
            self._crudo = crudo
            self._cambio = ahora
            if crudo == "varios":
                self._esperar_liberacion = True
                print("[IGNORADO] Varios botones a la vez. Suelte todos antes de continuar.", flush=True)
        # A brief electrical change does not count: it must hold for 30 ms.
        if ahora - self._cambio < .030:
            return None
        self._estable = crudo
        if crudo is None:
            self._esperar_liberacion = False
            return None
        if crudo == "varios" or self._esperar_liberacion:
            return None
        self._esperar_liberacion = True
        return crudo


class ControlHardware:
    """Facade over all the physical devices."""

    def __init__(self, programar_accion):
        self._programar = programar_accion
        self.pir = SensorPIR()
        self.botones = LectorBotones()
        self._lock_handle = None
        self._servo_chip = None
        self._servo_reclamado = False
        self._gpio_iniciado = False
        self._hardware_cerrado = False

    # ---- process lock ----
    def crear_lock(self):
        # Only one instance of the program may own the GPIO.
        self._lock_handle = open(LOCK_FILE, "a+")
        try:
            fcntl.flock(self._lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._lock_handle.close()
            self._lock_handle = None
            raise RuntimeError("El sistema de acceso ya está activo.")
        self._lock_handle.seek(0)
        self._lock_handle.truncate()
        self._lock_handle.write(LOCK_IDENTIFIER)
        self._lock_handle.flush()

    def limpiar_lock(self):
        # The file is not deleted: only the process lock is released.
        if self._lock_handle is not None:
            self._lock_handle.seek(0)
            self._lock_handle.truncate()
            self._lock_handle.close()
            self._lock_handle = None

    # ---- initialization ----
    def configurar_gpio(self):
        self._gpio_iniciado = True
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIR_PIN, GPIO.IN)

    def inicializar_hardware(self):
        for pin in PINES_BOTONES:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        for pin in (LED_VERDE, LED_ROJO, BUZZER):
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        self._servo_chip = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(self._servo_chip, SERVO, 0)
        self._servo_reclamado = True
        lgpio.tx_servo(self._servo_chip, SERVO, SERVO_REPOSO)
        print("Estabilizando PIR para botones: 30 segundos.")

    # ---- outputs ----
    def servo_reposo(self):
        lgpio.tx_servo(self._servo_chip, SERVO, SERVO_REPOSO)

    def tono_buzzer(self, duracion):
        GPIO.output(BUZZER, GPIO.HIGH)
        self._programar(int(duracion * 1000), lambda: GPIO.output(BUZZER, GPIO.LOW))

    def respuesta_hardware(self, resultado):
        # Opening lasts 3 s. A rejection returns to rest when the result
        # screen ends (4 s), through the standby reset.
        if resultado == "autorizado":
            pin = LED_VERDE
            lgpio.tx_servo(self._servo_chip, SERVO, SERVO_APERTURA)
            self._programar(3000, lambda: lgpio.tx_servo(self._servo_chip, SERVO, SERVO_REPOSO))
        else:
            pin = LED_ROJO
            if resultado in ("sin_permiso", "no_reconocido"):
                # Same rejection position as the original physical program: 0 degrees.
                lgpio.tx_servo(self._servo_chip, SERVO, SERVO_RECHAZO)
            else:
                lgpio.tx_servo(self._servo_chip, SERVO, SERVO_REPOSO)
        GPIO.output(pin, GPIO.HIGH)
        self._programar(1000, lambda: GPIO.output(pin, GPIO.LOW))
        if resultado == "error_sistema":
            self.tono_buzzer(1.0)
        else:
            self.tono_buzzer(0.1)
            self._programar(170, lambda: self.tono_buzzer(0.1))
            self._programar(340, lambda: self.tono_buzzer(0.1))

    def senal_captura_cancelada(self):
        GPIO.output(LED_ROJO, GPIO.HIGH)
        self.tono_buzzer(.25)
        self._programar(600, lambda: self.tono_buzzer(.25))
        self._programar(900, lambda: GPIO.output(LED_ROJO, GPIO.LOW))

    # ---- shutdown ----
    def cerrar_hardware(self):
        # It can be called from the window close handler and from finally:
        # cleaning up only once avoids releasing the same resources twice.
        if self._hardware_cerrado:
            return
        self._hardware_cerrado = True
        if self._servo_chip is not None:
            if self._servo_reclamado:
                try:
                    lgpio.tx_servo(self._servo_chip, SERVO, SERVO_REPOSO)
                    time.sleep(.25)
                    lgpio.tx_servo(self._servo_chip, SERVO, 0)
                    lgpio.gpio_free(self._servo_chip, SERVO)
                finally:
                    self._servo_reclamado = False
            lgpio.gpiochip_close(self._servo_chip)
            self._servo_chip = None
        if self._gpio_iniciado:
            GPIO.cleanup()
            self._gpio_iniciado = False