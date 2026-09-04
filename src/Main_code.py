from RPi import GPIO
import time

PIN_BOTON_1 = 18
PIN_BOTON_2 = 23
PIN_BOTON_3 = 24
GPIO.setmode(GPIO.BCM)

GPIO.setup(PIN_BOTON_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_BOTON_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_BOTON_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def revisar_boton(pin, valor):
    if GPIO.input(pin) == GPIO.LOW:
        print("BOTON PRESIONADO, valor =" , valor)
        while GPIO.input(pin) == GPIO.LOW:
            time.sleep(0.01)
        print("Boton liberado")
        time.sleep(0.2)
        return valor
    return None
secuencia = []

print("Programa iniciado")
print("Esperando que presiones los botones...")

try:
    while True:
        valor1 = revisar_boton(PIN_BOTON_1, 1)
        valor2 = revisar_boton(PIN_BOTON_2, 2)
        valor3 = revisar_boton(PIN_BOTON_3, 3)
        if valor1 is not None:
            secuencia.append(valor1)
        if valor2 is not None:
            secuencia.append(valor2)
        if valor3 is not None:
            secuencia.append(valor3)
        if len(secuencia) > 0:
            print("Secuencia actual:", secuencia)
        if len(secuencia) == 6:
            print("Se completaron 6 pulsaciones, secuencia lista:", secuencia)
            break
except KeyboardInterrupt:
    print("\nPrograma terminado")
finally:
    GPIO.cleanup()