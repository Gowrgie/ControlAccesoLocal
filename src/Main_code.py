from RPi import GPIO
import time
import hashlib
import os
import sys

PIN_BOTON_1 = 14
PIN_BOTON_2 = 15
PIN_BOTON_3 = 18

LED_VERDE = 23
LED_ROJO = 24
BUZZER = 25

TIEMPO_LIMITE_INACTIVIDAD = 4

ARCHIVO_PASSWORD = "password.txt"
ADMIN_PASSWORD = "admin123"
PASSWORD_INICIAL = [1, 2, 3, 1, 2, 3]


def calcular_hash(secuencia):
    texto = ",".join(str(numero) for numero in secuencia)
    return hashlib.sha256(texto.encode()).hexdigest()

def guardar_password(secuencia):
    with open(ARCHIVO_PASSWORD, "w") as archivo:
        archivo.write(calcular_hash(secuencia))

def leer_password_guardada():
    if not os.path.exists(ARCHIVO_PASSWORD):
        guardar_password(PASSWORD_INICIAL)
    with open(ARCHIVO_PASSWORD, "r") as archivo:
        return archivo.read().strip()

def verificar_password(secuencia):
    return calcular_hash(secuencia) == leer_password_guardada()

def cambiar_password():
    clave = input("Contraseña de administrador: ")
    if clave != ADMIN_PASSWORD:
        print("Clave de administrador incorrecta")
        return
    entrada = input("Nueva secuencia (ej: 123123): ")
    nueva_secuencia = [int(digito) for digito in entrada]
    print("Secuencia detectada:", " ".join(str(digito) for digito in nueva_secuencia))
    guardar_password(nueva_secuencia)
    print("Contraseña actualizada")


if len(sys.argv) > 1 and sys.argv[1] == "--admin":
    cambiar_password()
    sys.exit()


GPIO.setmode(GPIO.BCM)

GPIO.setup(PIN_BOTON_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_BOTON_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_BOTON_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(LED_VERDE, GPIO.OUT)
GPIO.setup(LED_ROJO, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)

buzzer_pwm = GPIO.PWM(BUZZER, 440)
GPIO.output(LED_VERDE, GPIO.LOW)
GPIO.output(LED_ROJO, GPIO.LOW)

def reproducir_tono(frecuencia, duracion):
    buzzer_pwm.ChangeFrequency(frecuencia)
    buzzer_pwm.start(50)
    time.sleep(duracion)
    buzzer_pwm.stop()


def revisar_boton(pin, valor):
    if GPIO.input(pin) == GPIO.LOW:
        print("BOTON PRESIONADO, valor =" , valor)
        reproducir_tono(1000, 0.05)
        while GPIO.input(pin) == GPIO.LOW:
            time.sleep(0.01)
        print("Boton liberado")
        time.sleep(0.2)
        return valor
    return None

def sonido_inicio_captura():
    reproducir_tono(800, 0.15)

def feedback_correcto():
    for _ in range(3):
        GPIO.output(LED_VERDE, GPIO.HIGH)
        reproducir_tono(1500, 0.12)
        GPIO.output(LED_VERDE, GPIO.LOW)
        time.sleep(0.15)

def feedback_incorrecto():
    for _ in range(3):
        GPIO.output(LED_ROJO, GPIO.HIGH)
        reproducir_tono(200, 0.12)
        GPIO.output(LED_ROJO, GPIO.LOW)
        time.sleep(0.15)

def feedback_timeout():
    GPIO.output(LED_ROJO, GPIO.HIGH)
    reproducir_tono(300, 0.3)
    GPIO.output(LED_ROJO, GPIO.LOW)

secuencia = []
tiempo_ultima_pulsacion = None
print("Programa iniciado")
print("Esperando que presiones los botones...")
sonido_inicio_captura()


try:
    while True:
        valor1 = revisar_boton(PIN_BOTON_1, 1)
        valor2 = revisar_boton(PIN_BOTON_2, 2)
        valor3 = revisar_boton(PIN_BOTON_3, 3)

        nueva_pulsacion = False

        if valor1 is not None:
            secuencia.append(valor1)
            nueva_pulsacion = True
        if valor2 is not None:
            secuencia.append(valor2)
            nueva_pulsacion = True
        if valor3 is not None:
            secuencia.append(valor3)
            nueva_pulsacion = True

        if nueva_pulsacion:
            print("Secuencia actual:", secuencia)
            tiempo_ultima_pulsacion = time.time()

        if len (secuencia) > 0 and len(secuencia) < 6:
            if tiempo_ultima_pulsacion is not None:
                tiempo_pasado = time.time() - tiempo_ultima_pulsacion
                if tiempo_pasado > TIEMPO_LIMITE_INACTIVIDAD:
                    print("Se excedio el limite de tiempo sin pulsaciones, se cancela la captura")
                    feedback_timeout()
                    secuencia = []
                    tiempo_ultima_pulsacion = None
                    print("Esperando que se presionen los botones...")
        if len(secuencia) == 6:
            print("Se completaron 6 pulsaciones, secuencia lista:", secuencia)

            if verificar_password(secuencia):
                print("Contraseña correcta")
                feedback_correcto()
            else:
                print("Contraseña incorrecta")
                feedback_incorrecto()

            secuencia = []
            tiempo_ultima_pulsacion = None
            print("Esperando nueva captura")
            sonido_inicio_captura()

except KeyboardInterrupt:
    print("\nPrograma terminado")
finally:
    buzzer_pwm.stop()
    GPIO.output(LED_VERDE, GPIO.LOW)
    GPIO.output(LED_ROJO, GPIO.LOW)
    GPIO.cleanup()