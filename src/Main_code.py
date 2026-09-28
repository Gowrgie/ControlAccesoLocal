from RPi import GPIO
import time
import sys
from db_conexion import validar_acceso 

PIN_BOTON_1 = 14
PIN_BOTON_2 = 15
PIN_BOTON_3 = 18

LED_VERDE = 23
LED_ROJO = 24
BUZZER = 25

TIEMPO_LIMITE_INACTIVIDAD = 4
LARGO_IDENTIFICADOR = 4  
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
        print("BOTON PRESIONADO, valor =", valor)
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


def feedback_falla():
    GPIO.output(LED_ROJO, GPIO.HIGH)
    reproducir_tono(200, 1.0)
    GPIO.output(LED_ROJO, GPIO.LOW)


def capturar_secuencia(largo_min, largo_max, tiempo_limite=TIEMPO_LIMITE_INACTIVIDAD):
    secuencia = []
    tiempo_ultima_pulsacion = None

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

        if len(secuencia) > 0 and len(secuencia) < largo_max:
            if tiempo_ultima_pulsacion is not None:
                tiempo_pasado = time.time() - tiempo_ultima_pulsacion
                if tiempo_pasado > tiempo_limite:
                    if len(secuencia) >= largo_min:
                        print("Pausa detectada con minimo cumplido, se toma como completa")
                        return secuencia
                    else:
                        print("Se acabo el tiempo sin llegar al minimo, se cancela")
                        feedback_timeout()
                        return None

        if len(secuencia) == largo_max:
            return secuencia


print("Programa iniciado")

try:
    while True:
        print("Esperando identificacion...")
        sonido_inicio_captura()

        identificador = capturar_secuencia(LARGO_IDENTIFICADOR, LARGO_IDENTIFICADOR)

        if identificador is None:
            continue  

        print("Identificador capturado, esperando clave...")

        clave = capturar_secuencia(4, 6)  

        if clave is None:
            continue

        identificador_str = "".join(str(numero) for numero in identificador)
        clave_str = "".join(str(numero) for numero in clave)

        resultado = validar_acceso(identificador_str, clave_str, "botones")

        if resultado == "autorizado":
            print("Acceso autorizado")
            feedback_correcto()
        elif resultado == "sin_permiso":
            print("Usuario reconocido pero sin permiso")
            feedback_incorrecto()

        elif resultado == "no_reconocido":
            print("Usuario no reconocido")
            feedback_incorrecto()

        elif resultado == "error_sistema":
            print("Fallo en el sistema, no se pudo validar")
            feedback_falla()


except KeyboardInterrupt:
    print("\nPrograma terminado")
finally:
    buzzer_pwm.stop()
    GPIO.output(LED_VERDE, GPIO.LOW)
    GPIO.output(LED_ROJO, GPIO.LOW)
    GPIO.cleanup()