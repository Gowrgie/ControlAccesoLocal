from RPi import GPIO
import lgpio
import time
import os
import sys
import atexit
import subprocess
from scripts_db.db_conexion import validar_acceso

# ============ CONFIGURACIÓN DE LOCK ============
LOCK_FILE = "/tmp/control_acceso.lock"
LOCK_IDENTIFIER = "botones"

PIR = 27

PIN_BOTON_1 = 14
PIN_BOTON_2 = 15
PIN_BOTON_3 = 18

LED_VERDE = 23
LED_ROJO = 24
BUZZER = 25

SERVO = 26

TIEMPO_LIMITE_INACTIVIDAD = 4  # RF-05
TIEMPO_ESTABILIZACION_PIR = 30
TIEMPO_APERTURA = 3  # RF-17

LARGO_IDENTIFICADOR = 4  # RF-02
LARGO_CLAVE_MIN = 4  # RF-02
LARGO_CLAVE_MAX = 6  # RF-02

PULSO_0 = 1000
PULSO_90 = 1500
PULSO_180 = 2000

BOTONES = {
    PIN_BOTON_1: 1,
    PIN_BOTON_2: 2,
    PIN_BOTON_3: 3
}


# ============ SISTEMA DE LOCK ============
def crear_lock():
    """Crea archivo lock para interfaz de botones. Verifica si interfaz gráfica está corriendo."""
    try:
        if os.path.exists(LOCK_FILE):
            with open(LOCK_FILE, 'r') as f:
                contenido = f.read().strip()
            if contenido == "interfaz_grafica":
                print("ERROR: La interfaz gráfica está activa.")
                print("No se puede usar la interfaz de botones simultáneamente.")
                sys.exit(1)

        # Crear el lock
        with open(LOCK_FILE, 'w') as f:
            f.write(LOCK_IDENTIFIER)
        print(f"Lock creado: {LOCK_FILE}")
    except Exception as e:
        print(f"Advertencia: Error al crear lock: {e}")


def limpiar_lock():
    """Elimina el archivo lock al cerrar."""
    try:
        if os.path.exists(LOCK_FILE):
            with open(LOCK_FILE, 'r') as f:
                if f.read().strip() == LOCK_IDENTIFIER:
                    os.remove(LOCK_FILE)
                    print(f"Lock eliminado: {LOCK_FILE}")
    except Exception as e:
        print(f"Error al limpiar lock: {e}")


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(PIN_BOTON_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # RF-14
GPIO.setup(PIN_BOTON_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # RF-14
GPIO.setup(PIN_BOTON_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # RF-14

GPIO.setup(PIR, GPIO.IN)  # RF-08

GPIO.setup(LED_VERDE, GPIO.OUT)  # RF-03
GPIO.setup(LED_ROJO, GPIO.OUT)  # RF-03
GPIO.setup(BUZZER, GPIO.OUT)  # RF-07

GPIO.output(LED_VERDE, GPIO.LOW)
GPIO.output(LED_ROJO, GPIO.LOW)
GPIO.output(BUZZER, GPIO.LOW)

servo_chip = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(servo_chip, SERVO, 0)  # RF-17


# ============ FUNCIONES DE AUDIO ============
def reproducir_sonido(archivo_sonido):
    """Reproduce un archivo de audio usando el sistema operativo."""
    try:
        # Intenta con aplay (Raspberry Pi por defecto)
        subprocess.run(['aplay', archivo_sonido], check=True,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (FileNotFoundError, subprocess.CalledProcessError):
        try:
            # Alternativa: paplay (PulseAudio)
            subprocess.run(['paplay', archivo_sonido], check=True,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass  # Si no hay audio, continúa sin error


def reproducir_tono(frecuencia=1000, duracion=0.5):
    """Genera un tono usando speaker-test."""
    try:
        os.system(f'(speaker-test -t sine -f {frecuencia} -l 1 & sleep {duracion}; killall speaker-test) 2>/dev/null &')
    except:
        pass


# ============ SERVO Y ACCESO ============
def mover_servo(angulo):
    if angulo == 0:
        pulso = PULSO_0
    elif angulo == 90:
        pulso = PULSO_90
    elif angulo == 180:
        pulso = PULSO_180
    else:
        print("Angulo de servo no valido:", angulo)
        return

    lgpio.tx_servo(servo_chip, SERVO, pulso)
    print("Servo ->", angulo, "grados")


def abrir_acceso():
    mover_servo(180)  # RF-17
    time.sleep(TIEMPO_APERTURA)  # RF-17
    mover_servo(90)  # RF-17


def pitido(duracion):
    GPIO.output(BUZZER, GPIO.HIGH)
    time.sleep(duracion)
    GPIO.output(BUZZER, GPIO.LOW)


def sonido_boton():
    pitido(0.04)


def sonido_inicio():
    pitido(0.07)
    time.sleep(0.05)
    pitido(0.07)


def sonido_espera():
    pitido(0.15)  # RF-06


def sonido_timeout():
    pitido(0.25)
    time.sleep(0.35)
    pitido(0.25)


def feedback_correcto():  # RF-03, RF-07
    """Feedback visual y de audio para acceso autorizado."""
    for _ in range(3):
        GPIO.output(LED_VERDE, GPIO.HIGH)
        pitido(0.10)
        GPIO.output(LED_VERDE, GPIO.LOW)
        time.sleep(0.07)

    # Reproducir sonido de éxito
    reproducir_tono(1000, 0.3)
    time.sleep(0.1)
    reproducir_tono(1200, 0.3)


def feedback_incorrecto():  # RF-03, RF-07
    """Feedback visual y de audio para acceso denegado."""
    for _ in range(3):
        GPIO.output(LED_ROJO, GPIO.HIGH)
        pitido(0.10)
        GPIO.output(LED_ROJO, GPIO.LOW)
        time.sleep(0.07)

    # Reproducir sonido de error
    reproducir_tono(500, 0.2)
    time.sleep(0.1)
    reproducir_tono(400, 0.2)


def feedback_falla():  # RF-07
    """Feedback de falla del sistema."""
    GPIO.output(LED_ROJO, GPIO.HIGH)
    pitido(1.0)
    GPIO.output(LED_ROJO, GPIO.LOW)

    # Sonido de alarma - dos tonos alternos
    reproducir_tono(800, 0.25)
    time.sleep(0.15)
    reproducir_tono(600, 0.25)


def captura_timeout():  # RF-05
    print("Pasaron 4 segundos sin actividad, se cancela la captura")
    GPIO.output(LED_ROJO, GPIO.HIGH)
    sonido_timeout()
    GPIO.output(LED_ROJO, GPIO.LOW)


def revisar_boton(pin, valor):
    if GPIO.input(pin) == GPIO.LOW:
        print("BOTON PRESIONADO, valor =", valor)
        sonido_boton()

        while GPIO.input(pin) == GPIO.LOW:
            time.sleep(0.01)

        print("Boton", valor, "liberado")
        time.sleep(0.05)  # RNF-01
        return valor
    return None


def capturar_secuencia(largo_min, largo_max):  # RF-02
    secuencia = []
    tiempo_ultima_actividad = time.monotonic()

    while True:
        for pin, valor in BOTONES.items():
            pulsacion = revisar_boton(pin, valor)

            if pulsacion is not None:
                secuencia.append(pulsacion)
                print("Secuencia actual:", secuencia)
                tiempo_ultima_actividad = time.monotonic()  # RF-05

                if len(secuencia) == largo_max:
                    return secuencia

        tiempo_sin_actividad = time.monotonic() - tiempo_ultima_actividad

        if tiempo_sin_actividad >= TIEMPO_LIMITE_INACTIVIDAD:  # RF-05
            if len(secuencia) >= largo_min:
                return secuencia
            else:
                captura_timeout()  # RF-05
                return None  # RF-05

        time.sleep(0.02)


def proceso_de_acceso():  # RF-15, RNF-07
    print()
    print("===== MOVIMIENTO DETECTADO =====")
    sonido_inicio()  # RF-08

    print("Ingresa tu identificador...")
    identificador = capturar_secuencia(LARGO_IDENTIFICADOR, LARGO_IDENTIFICADOR)  # RF-02
    if identificador is None:
        return

    print("Identificador capturado, ingresa tu clave...")
    clave = capturar_secuencia(LARGO_CLAVE_MIN, LARGO_CLAVE_MAX)  # RF-02
    if clave is None:
        return

    identificador_str = "".join(str(numero) for numero in identificador)
    clave_str = "".join(str(numero) for numero in clave)

    print("Validando...")
    resultado = validar_acceso(identificador_str, clave_str, "botones")  # RF-01, RF-11, RF-14, RNF-03

    if resultado == "autorizado":  # RF-13
        print("Acceso autorizado")
        feedback_correcto()
        abrir_acceso()  # RF-17

    elif resultado == "sin_permiso":  # RF-13
        print("Usuario reconocido pero sin permiso")
        feedback_incorrecto()

    elif resultado == "no_reconocido":  # RF-13
        print("Usuario no reconocido")
        feedback_incorrecto()

    else:  # RF-13
        print("Fallo del sistema, no se pudo validar")
        feedback_falla()


print()
print("===== SISTEMA DE CONTROL DE ACCESO =====")
print()

# Verificar y crear lock
crear_lock()
atexit.register(limpiar_lock)

print("Colocando servo en posicion de reposo...")
mover_servo(90)  # RF-17
time.sleep(1)

print("Estabilizando PIR, espera", TIEMPO_ESTABILIZACION_PIR, "segundos...")
time.sleep(TIEMPO_ESTABILIZACION_PIR)

while GPIO.input(PIR) == GPIO.HIGH:
    print("PIR todavia activo, esperando...")
    time.sleep(0.5)

print("Sistema armado. Esperando movimiento...")
sonido_espera()  # RF-06

pir_anterior = GPIO.LOW


try:
    while True:
        pir_actual = GPIO.input(PIR)  # RF-08, RNF-04

        if pir_actual == GPIO.HIGH and pir_anterior == GPIO.LOW:  # RF-08
            proceso_de_acceso()  # RNF-10

            print("Esperando que el PIR regrese a reposo...")
            while GPIO.input(PIR) == GPIO.HIGH:
                time.sleep(0.1)

            print("Esperando nuevo movimiento...")
            sonido_espera()  # RF-06, RF-04, RF-18
            pir_anterior = GPIO.LOW
        else:
            pir_anterior = pir_actual

        time.sleep(0.02)

except KeyboardInterrupt:
    print("\nPrograma detenido por el usuario")

finally:
    print("Liberando GPIO...")
    GPIO.output(LED_VERDE, GPIO.LOW)
    GPIO.output(LED_ROJO, GPIO.LOW)
    GPIO.output(BUZZER, GPIO.LOW)

    lgpio.tx_servo(servo_chip, SERVO, 0)
    lgpio.gpio_free(servo_chip, SERVO)
    lgpio.gpiochip_close(servo_chip)

    GPIO.cleanup()
    print("Programa finalizado")