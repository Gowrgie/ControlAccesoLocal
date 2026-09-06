from RPi import GPIO
import time

PIN_BOTON_1 = 14
PIN_BOTON_2 = 15
PIN_BOTON_3 = 18

LED_VERDE = 23
LED_ROJO = 24
BUZZER = 25

PASSWORD_VALIDA = [1, 2, 3, 1, 2, 3]


GPIO.setmode(GPIO.BCM)

GPIO.setup(PIN_BOTON_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_BOTON_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_BOTON_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(LED_VERDE, GPIO.OUT)
GPIO.setup(LED_ROJO, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)

GPIO.output(LED_VERDE, GPIO.LOW)
GPIO.output(LED_ROJO, GPIO.LOW)
GPIO.output(BUZZER, GPIO.LOW)


def revisar_boton(pin, valor):
    if GPIO.input(pin) == GPIO.LOW:
        print("BOTON PRESIONADO, valor =" , valor)
        while GPIO.input(pin) == GPIO.LOW:
            time.sleep(0.01)
        print("Boton liberado")
        time.sleep(0.2)
        return valor
    return None

def sonido_inicio_captura():
    GPIO.output(BUZZER, GPIO.HIGH)
    time.sleep(0.15)
    GPIO.output(BUZZER, GPIO.LOW)

def feedback_correcto():
    for _ in range(3):
        GPIO.output(LED_VERDE, GPIO.HIGH)
        time.sleep(0.15)
        GPIO.output(LED_VERDE, GPIO.LOW)
        time.sleep(0.15)

def feedback_incorrecto():
    for _ in range(3):
        GPIO.output(LED_ROJO, GPIO.HIGH)
        time.sleep(0.15)
        GPIO.output(LED_ROJO, GPIO.LOW)
        time.sleep(0.15)


secuencia = []

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

        if len(secuencia) == 6:
            print("Se completaron 6 pulsaciones, secuencia lista:", secuencia)

            if secuencia == PASSWORD_VALIDA:
                print("Contraseña correcta")
                feedback_correcto()
            else:
                print("Contraseña incorrecta")
                feedback_incorrecto()

            secuencia = []
            print("Esperando nueva captura")
            sonido_inicio_captura()

except KeyboardInterrupt:
    print("\nPrograma terminado")
finally:
    GPIO.output(LED_VERDE, GPIO.LOW)
    GPIO.output(LED_ROJO, GPIO.LOW)
    GPIO.output(BUZZER, GPIO.LOW)
    GPIO.cleanup()