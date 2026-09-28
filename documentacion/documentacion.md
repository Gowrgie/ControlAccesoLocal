# Documentación del equipo de hardware

## Proyecto Integrativo 1

### Control de acceso local con Raspberry Pi

---

## 1. Objetivo del equipo de hardware

El equipo de hardware tiene como objetivo implementar la parte física del sistema de control de acceso mediante botones conectados a una Raspberry Pi 5.

Cada botón representará un valor diferente que posteriormente será utilizado por el programa para formar una secuencia de acceso.

La función principal del equipo de hardware es conseguir que las pulsaciones físicas realizadas por el usuario puedan ser detectadas correctamente por la Raspberry Pi y posteriormente enviadas al programa desarrollado por el equipo de software.

### Elementos utilizados para el sistema

Para la creación del sistema se utilizaron los siguientes elementos:

- Raspberry Pi 5.
- Monitor.
- Teclado.
- Mouse.
- Fuente de alimentación.
- Conexión de red.
- 1 Protoboard.
- 7 Cables jumper.
- 3 Cables rígidos para protoboard
- 3 Botones físicos.

Posteriormente, conforme avanzó el desarrollo, también se incorporaron:

- 1 LED verde.
- 3 Resistencias de 220 Ω
- 1 LED rojo.
- 1 Buzzer.

Estos componentes se fueron agregando de manera progresiva de acuerdo con las necesidades del prototipo.

En las primeras etapas, el objetivo principal fue comprobar el funcionamiento de la Raspberry Pi, establecer la conexión remota y realizar pruebas de lectura mediante un solo botón.

Después de validar esa parte, se incorporaron los demás botones y los indicadores visuales y auditivos.

---

## 2. Preparación inicial de la Raspberry Pi

Como primera actividad se preparó una Raspberry Pi 5 para utilizarla como plataforma principal del prototipo.

La Raspberry Pi cuenta con el sistema operativo Ubuntu instalado.

Durante la preparación inicial se conectaron los siguientes elementos:

- monitor;
- teclado;
- mouse;
- alimentación;
- conexión de red.

El primer objetivo fue comprobar que la Raspberry Pi encendiera correctamente y que Ubuntu iniciara sin problemas.

Una vez confirmado el funcionamiento del sistema operativo, se decidió administrar la Raspberry Pi de forma remota mediante SSH.

---

## 3. Configuración de acceso remoto y preparación del entorno

Después de comprobar que Ubuntu funcionaba correctamente, se estableció una conexión remota mediante SSH.

SSH permite controlar la Raspberry Pi desde otra computadora mediante una terminal, siempre que ambos equipos tengan conectividad de red.

La conexión se realiza utilizando un comando similar a:

```bash
ssh usuario@IP_DE_LA_RASPBERRY
```

Por ejemplo:

```bash
ssh usuario@192.168.1.100
```

Una vez establecida la conexión, la terminal de la computadora remota permite ejecutar comandos directamente sobre Ubuntu.

Durante el desarrollo se utiliza SSH para:

- instalar paquetes;
- crear archivos;
- editar código;
- ejecutar programas;
- revisar errores;
- administrar Ubuntu;
- realizar pruebas sin utilizar directamente monitor, teclado y mouse en la Raspberry Pi.

A partir de este punto, la mayor parte de las pruebas relacionadas con hardware se realizaron mediante la conexión SSH.

### Actualización de Ubuntu

Antes de instalar las herramientas necesarias se actualizaron los repositorios del sistema mediante:

```bash
sudo apt update
```

Este comando actualiza la lista de paquetes disponibles para Ubuntu.

No instala todavía las librerías del proyecto, sino que permite que el sistema consulte las versiones disponibles en sus repositorios.

### Instalación de bibliotecas para GPIO

Para poder trabajar con los GPIO desde Python se instalaron las siguientes bibliotecas:

```bash
sudo apt install -y python3-gpiozero python3-lgpio
```

Con este comando se instalaron principalmente:

- `gpiozero`;
- `lgpio`.

### gpiozero

`gpiozero` es una biblioteca de Python diseñada para facilitar el uso de los pines GPIO de una Raspberry Pi.

Permite trabajar con componentes físicos mediante clases sencillas.

Por ejemplo:

```python
from gpiozero import Button
```

Con esta biblioteca es posible representar un botón físico mediante:

```python
boton = Button(18)
```

También permite manejar opciones útiles como resistencias pull-up y control de rebote.

Por ejemplo:

```python
Button(18, pull_up=True, bounce_time=0.2)
```

### lgpio

`lgpio` es una biblioteca que permite acceder a los GPIO disponibles en sistemas Linux.

En la primera implementación se esperaba que funcionara como una capa intermedia entre `gpiozero`, Ubuntu y el hardware físico.

La comunicación planteada era:

```text
Programa en Python
        ↓
gpiozero
        ↓
lgpio
        ↓
Ubuntu
        ↓
GPIO de Raspberry Pi
        ↓
Botón físico
```

### Verificación de las bibliotecas

Después de la instalación se comprobó que Python pudiera importar correctamente las librerías.

Para `gpiozero` se utilizó:

```bash
python3 -c "import gpiozero; print('gpiozero instalado correctamente')"
```

Para `lgpio` se utilizó:

```bash
python3 -c "import lgpio; print('lgpio instalado correctamente')"
```

Estas pruebas permitieron comprobar que ambas bibliotecas estaban instaladas antes de comenzar con la programación del botón.

---

## 4. Identificación de los GPIO

Una vez preparada la Raspberry Pi y establecido el entorno de trabajo, el siguiente paso fue identificar cómo conectar los botones físicos.

Para ello fue necesario comprender el funcionamiento de los pines GPIO.

GPIO significa:

**General Purpose Input/Output**

En español:

**Entrada/Salida de Propósito General**

Los GPIO permiten que la Raspberry Pi interactúe con dispositivos físicos externos.

Estos pines pueden utilizarse como:

- entradas;
- salidas.

En este proyecto se utilizarán principalmente como entradas, ya que los botones deberán enviar una señal a la Raspberry Pi cuando sean presionados.

El flujo esperado es:

```text
Usuario presiona un botón
        ↓
Cambia el estado eléctrico del GPIO
        ↓
La Raspberry Pi detecta el cambio
        ↓
El programa recibe la pulsación
        ↓
Se registra el valor correspondiente
```

---

## 5. Diferencia entre GPIO y pin físico

Antes de realizar la conexión fue necesario identificar la diferencia entre la numeración física de los pines y la numeración BCM.

Por ejemplo:

```text
GPIO18 = pin físico 12
```

Esto significa que físicamente el cable se conecta en el pin número 12 del conector de 40 pines, pero en Python se hace referencia al GPIO mediante el número 18.

Por ejemplo:

```python
Button(18)
```

Por lo tanto, es importante no confundir:

```text
GPIO18
```

con:

```text
pin físico 18
```

ya que representan posiciones diferentes.

Para el programa se decidió utilizar numeración BCM.

---

## 6. Primera conexión realizada

Después de identificar los GPIO, se decidió realizar una primera prueba utilizando solamente un botón.

La intención fue comprobar primero que la Raspberry Pi pudiera detectar una pulsación antes de conectar los tres botones requeridos por el proyecto.

Inicialmente se realizaron conexiones hacia:

- pin físico 2;
- pin físico 6;
- un GPIO.

Posteriormente se identificó que el pin físico 2 proporciona 5 V y que esta conexión no era necesaria para leer el botón.

Debido a que los GPIO de la Raspberry Pi trabajan con niveles lógicos de 3.3 V, se decidió retirar la conexión de 5 V para evitar riesgos sobre la entrada GPIO.

La conexión final de prueba quedó formada únicamente por:

- GPIO18;
- botón;
- GND.

---

## 7. Conexión utilizada para el primer botón

Para esta prueba se seleccionó:

| Función | GPIO | Pin físico |
|---|---:|---:|
| Entrada del botón | GPIO18 | 12 |
| Tierra | GND | 6 |

La conexión utilizada es:

```text
GPIO18 (pin físico 12)
        │
        │
     [ BOTÓN ]
        │
        │
GND (pin físico 6)
```

De forma simplificada:

```text
GPIO18 ─── Botón ─── GND
```

No se utiliza conexión directa a 5 V para esta prueba.

---

## 8. Montaje del botón en protoboard

Para realizar la conexión física se utilizó una protoboard.

La protoboard permite realizar conexiones eléctricas temporales sin necesidad de soldar.

El botón fue colocado atravesando la separación central de la protoboard.

Esto es importante debido a la forma en que los contactos internos de la protoboard están conectados.

De manera simplificada:

```text
a ●
b ●
c ●
d ●
e ●
──────── separación central ────────
f ●
g ●
h ●
i ●
j ●
```

Los grupos de cinco puntos de cada lado se encuentran conectados internamente.

El botón se colocó de manera que sus contactos quedaran separados correctamente a ambos lados de la ranura central.

Esto permite que el botón funcione como un interruptor entre GPIO18 y GND.

---

## 9. Funcionamiento eléctrico del botón

Después de realizar la conexión fue necesario definir cómo sería detectado el botón desde el programa.

Se decidió utilizar una configuración de tipo:

```text
pull-up
```

En esta configuración, el GPIO permanece normalmente en estado HIGH.

Cuando el botón no está presionado:

```text
Botón sin presionar
        ↓
Circuito abierto
        ↓
GPIO en estado HIGH
        ↓
Valor lógico 1
```

Cuando el usuario presiona el botón:

```text
Botón presionado
        ↓
GPIO conectado a GND
        ↓
GPIO en estado LOW
        ↓
Valor lógico 0
```

El programa detecta este cambio de HIGH a LOW y lo interpreta como una pulsación.

---

## 10. Creación del primer programa de prueba

Una vez realizada la conexión física y preparadas las bibliotecas, se creó un programa de prueba para intentar detectar el botón.

Se creó el archivo:

```text
prueba_boton.py
```

La primera versión del programa utilizó `gpiozero`:

```python
from gpiozero import Button
from signal import pause

boton = Button(18, pull_up=True, bounce_time=0.2)

def boton_presionado():
    print("Botón presionado")

def boton_liberado():
    print("Botón liberado")

boton.when_pressed = boton_presionado
boton.when_released = boton_liberado

print("Programa iniciado")
print("Esperando que presiones el botón...")

pause()
```

El objetivo era que la terminal mostrara un mensaje cada vez que el botón fuera presionado o liberado.

---

## 11. Rebote del botón

Durante la creación del programa se incorporó el manejo del rebote físico del pulsador.

Un botón físico no siempre genera una sola transición eléctrica perfecta.

Cuando se presiona, los contactos pueden realizar varias pequeñas conexiones y desconexiones durante un periodo muy corto.

Este fenómeno se conoce como:

```text
rebote
```

Si no se controla, una pulsación física puede ser interpretada por el programa como varias pulsaciones.

Para reducir este problema, en la primera versión con `gpiozero` se utilizó:

```python
bounce_time=0.2
```

Esto establece un periodo aproximado de 0.2 segundos para evitar registros duplicados producidos por el rebote.

Esta característica está relacionada con el requerimiento:

```text
RNF-01. El sistema evitará registrar una pulsación física debido al rebote del botón.
```

---

## 12. Primera ejecución del programa

Después de crear el archivo se ejecutó mediante SSH utilizando:

```bash
GPIOZERO_PIN_FACTORY=lgpio python3 prueba_boton.py
```

El resultado esperado era:

```text
Programa iniciado
Esperando que presiones el botón...
```

Después de presionar el botón debía mostrarse:

```text
Botón presionado
```

Y al liberarlo:

```text
Botón liberado
```

Sin embargo, durante esta prueba se presentó un error antes de que el programa pudiera leer físicamente el botón.

---

## 13. Error encontrado durante la primera prueba

Durante la ejecución se presentó el siguiente mensaje:

```text
lgpio.error: 'can not open gpiochip'
```

El programa no consiguió acceder correctamente al dispositivo GPIO de Ubuntu.

Debido a que el error ocurre al inicializar la biblioteca, el sistema no llegó a la etapa de lectura física del botón.

Por esta razón, la primera implementación con `gpiozero` y `lgpio` no pudo utilizarse para comprobar la pulsación.

---

## 14. Cambio de biblioteca y programa de prueba

Después del error presentado con `gpiozero`, se decidió cambiar la forma en que Python accedería a los GPIO.

Se optó por utilizar una implementación compatible con `RPi.GPIO`.

Para ello se instaló:

```bash
sudo apt install -y python3-rpi-lgpio
```

Después se verificó que Python pudiera importar correctamente la biblioteca mediante:

```bash
python3 -c "from RPi import GPIO; print('GPIO instalado correctamente')"
```

Una vez comprobada la instalación, se modificó el archivo `prueba_boton.py`.

### Nuevo programa utilizado

El programa fue reemplazado por:

```python
from RPi import GPIO
import time

# Estamos utilizando GPIO18 = pin físico 12
PIN_BOTON = 18

# Utilizamos numeración BCM
GPIO.setmode(GPIO.BCM)

# Configuramos GPIO18 como entrada
# La resistencia pull-up interna mantiene el pin en HIGH
GPIO.setup(
    PIN_BOTON,
    GPIO.IN,
    pull_up_down=GPIO.PUD_UP
)

print("Programa iniciado")
print("Esperando que presiones el botón...")

try:
    while True:

        # Cuando el botón conecta GPIO18 con GND,
        # el estado cambia a LOW
        if GPIO.input(PIN_BOTON) == GPIO.LOW:

            print("BOTÓN PRESIONADO")

            # Esperamos a que se suelte
            while GPIO.input(PIN_BOTON) == GPIO.LOW:
                time.sleep(0.01)

            print("Botón liberado")

            # Pequeño debounce
            time.sleep(0.2)

except KeyboardInterrupt:
    print("\nPrograma terminado")

finally:
    GPIO.cleanup()
```

### Funcionamiento del nuevo programa

Primero se importa:

```python
from RPi import GPIO
```

Esta biblioteca permite configurar y consultar directamente los GPIO desde Python.

Después se define el GPIO utilizado:

```python
PIN_BOTON = 18
```

Este número corresponde a:

```text
GPIO18 = pin físico 12
```

Posteriormente se establece la numeración BCM:

```python
GPIO.setmode(GPIO.BCM)
```

Esto indica que los números usados en el código representan GPIO y no posiciones físicas del conector.

### Configuración del GPIO como entrada

El GPIO se configura mediante:

```python
GPIO.setup(
    PIN_BOTON,
    GPIO.IN,
    pull_up_down=GPIO.PUD_UP
)
```

`GPIO.IN` indica que GPIO18 funcionará como entrada.

La opción:

```python
GPIO.PUD_UP
```

activa la resistencia pull-up interna.

Por lo tanto, cuando el botón no está presionado, GPIO18 permanece en:

```text
HIGH
```

Cuando el usuario lo presiona y conecta GPIO18 con GND, cambia a:

```text
LOW
```

El programa detecta la pulsación mediante:

```python
if GPIO.input(PIN_BOTON) == GPIO.LOW:
```

Cuando esto ocurre se muestra:

```text
BOTÓN PRESIONADO
```

### Detección de la liberación del botón

Después de detectar la pulsación se utiliza:

```python
while GPIO.input(PIN_BOTON) == GPIO.LOW:
    time.sleep(0.01)
```

Mientras el botón continúa presionado, el GPIO permanece en LOW.

Cuando el usuario lo libera, vuelve a HIGH y el ciclo termina.

En ese momento se muestra:

```text
Botón liberado
```

### Control del rebote en el nuevo programa

En la primera versión se utilizaba:

```python
bounce_time=0.2
```

Al cambiar de implementación, el control del rebote se realizó manualmente mediante:

```python
time.sleep(0.2)
```

Después de registrar y liberar el botón, el programa espera 0.2 segundos antes de continuar.

Esto ayuda a evitar que pequeñas variaciones eléctricas del pulsador sean interpretadas como nuevas pulsaciones.

### Finalización del programa

El programa se mantiene ejecutándose mediante:

```python
while True:
```

Para detenerlo desde la terminal puede utilizarse:

```text
Ctrl + C
```

La interrupción es manejada mediante:

```python
except KeyboardInterrupt:
```

Finalmente se ejecuta:

```python
GPIO.cleanup()
```

Esta instrucción libera la configuración de los GPIO al terminar el programa.

---

## 15. Flujo del nuevo programa

El funcionamiento de la segunda versión puede resumirse así:

```text
Iniciar programa
        ↓
Configurar GPIO18 como entrada
        ↓
Activar resistencia pull-up
        ↓
GPIO18 permanece en HIGH
        ↓
Esperar pulsación
        ↓
Usuario presiona botón
        ↓
GPIO18 cambia a LOW
        ↓
Mostrar "BOTÓN PRESIONADO"
        ↓
Esperar a que el usuario libere el botón
        ↓
GPIO18 vuelve a HIGH
        ↓
Mostrar "Botón liberado"
        ↓
Esperar 0.2 segundos
        ↓
Volver a esperar una pulsación
```

La conexión física continúa siendo:

```text
GPIO18 (pin físico 12) ─── Botón ─── GND (pin físico 6)
```

---

## 16. Estado actual del equipo de hardware

Hasta este punto se han completado las siguientes actividades:

- [x] Preparación física de la Raspberry Pi 5.
- [x] Instalación y comprobación de Ubuntu.
- [x] Conexión de la Raspberry Pi a la red.
- [x] Configuración y prueba de acceso mediante SSH.
- [x] Actualización de los repositorios de Ubuntu.
- [x] Instalación de `gpiozero`.
- [x] Instalación de `lgpio`.
- [x] Verificación de las bibliotecas desde Python.
- [x] Identificación del funcionamiento de los GPIO.
- [x] Identificación de la diferencia entre numeración física y BCM.
- [x] Selección de GPIO18 para la primera prueba.
- [x] Identificación de GPIO18 como pin físico 12.
- [x] Selección de GND en el pin físico 6.
- [x] Montaje de un botón sobre protoboard.
- [x] Primera conexión física del pulsador.
- [x] Identificación y retiro de la conexión innecesaria de 5 V.
- [x] Configuración del botón mediante esquema pull-up.
- [x] Creación de `prueba_boton.py`.
- [x] Primera implementación mediante `gpiozero`.
- [x] Incorporación inicial de control de rebote.
- [x] Ejecución del primer programa.
- [x] Identificación del error `can not open gpiochip`.
- [x] Instalación de `python3-rpi-lgpio`.
- [x] Cambio de implementación hacia `RPi.GPIO`.
- [x] Creación de una segunda versión de `prueba_boton.py`.
- [x] Implementación manual del control de rebote.
- [x] Confirmar definitivamente la lectura física del primer botón.
- [x] Incorporar el segundo botón.
- [x] Incorporar el tercer botón.
- [x] Realizar la integración con el programa principal.

---

## 17. Comprobación del funcionamiento del primer botón

Después de modificar la implementación para utilizar `RPi.GPIO`, se realizó nuevamente la prueba física del primer botón.

El resultado obtenido en terminal fue el esperado:

```text
Programa iniciado
Esperando que presiones el botón...

BOTÓN PRESIONADO
Botón liberado
```
---

## 18. Configuración de los tres botones

De momento, la configuración prevista es:

| Botón | Valor | GPIO BCM | Pin físico |
|---|---:|---:|---:|
| Botón 1 | 1 | GPIO14 | 8 |
| Botón 2 | 2 | GPIO15 | 10 |
| Botón 3 | 3 | GPIO18 | 12 |
| Tierra | - | GND | 6 |

Cada botón representará un valor distinto que posteriormente será enviado al programa principal.

El comportamiento esperado será:

```text
Botón 1 presionado → 1
Botón 2 presionado → 2
Botón 3 presionado → 3
```

---

## 19. Relación con los requerimientos

El trabajo desarrollado por el equipo de hardware se alinea con los requerimientos del proyecto. La matriz completa y oficial de trazabilidad con el detalle de issues, PRs y evidencias se encuentra documentada en [../traceability.md](../traceability.md).

A continuación se resume brevemente el alcance del hardware respecto a los requerimientos clave abordados:

### RF-01

> El sistema deberá capturar la secuencia introducida, compararla con una clave válida y determinar si el acceso se autoriza o se rechaza.

El equipo de hardware proporciona los dispositivos físicos mediante los cuales el usuario introducirá la secuencia.

### RF-02

> El sistema capturará una clave de 4 a 6 pulsaciones.

Los botones permitirán generar las pulsaciones necesarias para formar la clave (el prototipo físico captura una secuencia de 6 pulsaciones).

### RNF-01

> El sistema evitará registrar una pulsación física debido al rebote del botón.

En la primera implementación se utilizó:

```python
bounce_time=0.2
```

Posteriormente, en la implementación basada en `RPi.GPIO`, se utilizó:

```python
time.sleep(0.2)
```

para reducir la posibilidad de detectar varias veces una misma pulsación física.

---

## 20. Flujo del trabajo realizado

Hasta este punto, el proceso seguido por el equipo de hardware puede resumirse de la siguiente manera:

```text
Preparación de Raspberry Pi 5
        ↓
Instalación y prueba de Ubuntu
        ↓
Configuración de red
        ↓
Conexión por SSH
        ↓
Actualización de Ubuntu
        ↓
Instalación de gpiozero y lgpio
        ↓
Identificación de GPIO
        ↓
Selección de GPIO18
        ↓
Montaje del botón en protoboard
        ↓
Conexión GPIO18 → botón → GND
        ↓
Creación de prueba_boton.py
        ↓
Primera implementación con gpiozero
        ↓
Ejecución del programa
        ↓
Error: can not open gpiochip
        ↓
Instalación de python3-rpi-lgpio
        ↓
Cambio a RPi.GPIO
        ↓
Creación de segundo programa
        ↓
Implementación de lectura LOW/HIGH
        ↓
Implementación manual de debounce
        ↓
Lectura física confirmada
        ↓
Integración de los tres botones
```

---

## 21. Conclusión del avance

El equipo de hardware logró preparar la Raspberry Pi 5, instalar y utilizar Ubuntu, establecer una conexión remota mediante SSH y realizar el primer montaje físico de un botón.

Durante el proceso se identificaron conceptos necesarios para continuar el desarrollo, entre ellos GPIO, numeración BCM, GND, resistencias pull-up, funcionamiento de la protoboard y rebote de botones.

También se preparó Ubuntu con las bibliotecas necesarias para trabajar con GPIO desde Python.

La primera implementación utilizó `gpiozero` y `lgpio`, pero durante la ejecución se presentó el error:

```text
lgpio.error: 'can not open gpiochip'
```

Debido a este problema se cambió la implementación y se instaló `python3-rpi-lgpio` para utilizar una interfaz compatible con `RPi.GPIO`.

Posteriormente se creó una segunda versión del programa, en la cual GPIO18 se configura directamente como entrada con una resistencia pull-up interna y se detectan los estados HIGH y LOW del botón.

La segunda implementación permitió comprobar correctamente la lectura física del primer botón.

A partir de este resultado se continuó con la incorporación de los otros dos pulsadores y con las pruebas de captura de secuencias.

Posteriormente se comprobó que los tres botones podían ser detectados correctamente y que cada uno podía asociarse con un valor distinto.

---

## 22. Prueba de funcionamiento con tres botones

Una vez comprobado el funcionamiento correcto de un solo botón, el siguiente paso fue extender la prueba para trabajar con los tres botones requeridos por el sistema.

Para esta etapa se utilizaron los siguientes GPIO:

| Botón | Valor | GPIO BCM |
|---|---:|---:|
| Botón 1 | 1 | GPIO14 |
| Botón 2 | 2 | GPIO15 |
| Botón 3 | 3 | GPIO18 |

Cada botón se configuró como entrada con resistencia pull-up interna.

El código utilizado fue:

```python
from RPi import GPIO
import time

PIN_BOTON_1 = 14
PIN_BOTON_2 = 15
PIN_BOTON_3 = 18

GPIO.setmode(GPIO.BCM)

GPIO.setup(PIN_BOTON_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_BOTON_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_BOTON_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def revisar_boton(pin, valor):
    if GPIO.input(pin) == GPIO.LOW:
        print("BOTON PRESIONADO, valor =", valor)

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
            print(
                "Se completaron 6 pulsaciones, secuencia lista:",
                secuencia
            )
            break

except KeyboardInterrupt:
    print("\nPrograma terminado")

finally:
    GPIO.cleanup()
```

### Resultado de la prueba

La prueba permitió comprobar que:

- los tres botones fueron detectados correctamente;
- cada botón podía distinguirse de los demás;
- cada pulsador generaba el valor asignado;
- los valores podían almacenarse dentro de una secuencia;
- el sistema podía detectar cuando se completaban seis pulsaciones.

Por ejemplo:

```text
Botón 1 → 1
Botón 2 → 2
Botón 3 → 3
```

Durante esta prueba también se detectó un detalle en la salida del programa.

La condición:

```python
if len(secuencia) > 0:
    print("Secuencia actual:", secuencia)
```

provocaba que la secuencia se imprimiera continuamente dentro del ciclo principal, incluso cuando no se registraba una nueva pulsación.

Este comportamiento no impedía detectar los botones, pero generaba una salida repetitiva innecesaria.

Por esta razón se decidió corregirlo en la siguiente versión.

---

## 23. Corrección de la impresión repetitiva

Después de comprobar que los tres botones funcionaban correctamente, se modificó la lógica para que la secuencia solo se mostrara cuando realmente se registrara una nueva pulsación.

Para ello se agregó una variable de control:

```python
nueva_pulsacion = False
```

Cuando alguno de los botones era detectado, además de agregar su valor a la secuencia se modificaba la variable:

```python
if valor1 is not None:
    secuencia.append(valor1)
    nueva_pulsacion = True
```

El mismo procedimiento se aplicó para los otros dos botones.

Posteriormente, la secuencia únicamente se imprimía mediante:

```python
if nueva_pulsacion:
    print("Secuencia actual:", secuencia)
```

Con este cambio se eliminó la impresión repetitiva que se producía en la versión anterior.

---

## 24. Integración de indicadores LED y buzzer

Después de comprobar la lectura estable de los tres botones, se decidió incorporar elementos físicos adicionales para proporcionar retroalimentación al usuario.

Se agregaron:

- un LED verde;
- un LED rojo;
- un buzzer.

Los LED se conectaron utilizando resistencias de 220 Ω para limitar la corriente y proteger tanto los LED como las salidas GPIO de la Raspberry Pi.

Estos componentes permiten comunicar físicamente el estado del sistema.

La configuración utilizada fue:

```python
LED_VERDE = 23
LED_ROJO = 24
BUZZER = 25
```

También se definió una contraseña válida:

```python
PASSWORD_VALIDA = [1, 2, 3, 1, 2, 3]
```

La clave contiene seis pulsaciones.

### Configuración de las salidas

Los LED y el buzzer se configuraron como salidas:

```python
GPIO.setup(LED_VERDE, GPIO.OUT)
GPIO.setup(LED_ROJO, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)
```

Inicialmente se mantuvieron apagados:

```python
GPIO.output(LED_VERDE, GPIO.LOW)
GPIO.output(LED_ROJO, GPIO.LOW)
GPIO.output(BUZZER, GPIO.LOW)
```

### Sonido de inicio de captura

Se creó una función para generar una señal cuando el sistema estuviera listo para capturar una nueva secuencia:

```python
def sonido_inicio_captura():
    GPIO.output(BUZZER, GPIO.HIGH)
    time.sleep(0.15)
    GPIO.output(BUZZER, GPIO.LOW)
```

Esta función permite que el usuario sepa que el sistema se encuentra esperando una nueva clave.

### Indicador de acceso correcto

Para indicar que una secuencia coincide con la contraseña válida se creó:

```python
def feedback_correcto():
    for _ in range(3):
        GPIO.output(LED_VERDE, GPIO.HIGH)
        time.sleep(0.15)
        GPIO.output(LED_VERDE, GPIO.LOW)
        time.sleep(0.15)
```

El LED verde parpadea tres veces para indicar un acceso autorizado.

### Indicador de acceso incorrecto

Para una contraseña incorrecta se creó:

```python
def feedback_incorrecto():
    for _ in range(3):
        GPIO.output(LED_ROJO, GPIO.HIGH)
        time.sleep(0.15)
        GPIO.output(LED_ROJO, GPIO.LOW)
        time.sleep(0.15)
```

El LED rojo parpadea tres veces para indicar un acceso denegado.

### Comparación de la contraseña

Una vez completadas las seis pulsaciones se realiza la comparación:

```python
if secuencia == PASSWORD_VALIDA:
    print("Contraseña correcta")
    feedback_correcto()
else:
    print("Contraseña incorrecta")
    feedback_incorrecto()
```

Después de la validación, la secuencia se reinicia:

```python
secuencia = []
```

El sistema vuelve entonces al estado de espera:

```python
print("Esperando nueva captura")
sonido_inicio_captura()
```

### Resultado de la prueba

La integración funcionó correctamente.

Se comprobó que:

- los tres botones continuaban siendo detectados;
- la secuencia podía capturarse correctamente;
- una secuencia válida activaba el LED verde;
- una secuencia incorrecta activaba el LED rojo;
- el buzzer indicaba el inicio de una nueva captura;
- el sistema permitía ingresar una nueva secuencia después de cada intento.

---

## 25. Implementación de sonidos diferentes mediante PWM

Después de comprobar el funcionamiento básico del buzzer, se decidió mejorar la retroalimentación auditiva.

En lugar de utilizar solamente estados HIGH y LOW, se utilizó PWM para generar distintas frecuencias.

Se creó un objeto PWM:

```python
buzzer_pwm = GPIO.PWM(BUZZER, 440)
```

PWM significa:

**Pulse Width Modulation**

En español:

**Modulación por ancho de pulso**

En este caso se utiliza para generar diferentes frecuencias en el buzzer y producir tonos distintos.

### Función para reproducir tonos

Se creó la siguiente función:

```python
def reproducir_tono(frecuencia, duracion):
    buzzer_pwm.ChangeFrequency(frecuencia)
    buzzer_pwm.start(50)
    time.sleep(duracion)
    buzzer_pwm.stop()
```

La función recibe:

- `frecuencia`: frecuencia del sonido en Hz;
- `duracion`: tiempo durante el cual se reproduce.

### Sonido al presionar un botón

Cada pulsación genera un tono corto:

```python
reproducir_tono(1000, 0.05)
```

Esto proporciona una confirmación auditiva inmediata de que el botón fue detectado.

### Sonido de inicio de captura

Se configuró:

```python
reproducir_tono(800, 0.15)
```

Este sonido indica que el sistema está listo para recibir una nueva secuencia.

### Sonido de acceso correcto

Durante el parpadeo del LED verde se reproduce:

```python
reproducir_tono(1500, 0.12)
```

La frecuencia más alta permite diferenciar el resultado correcto.

### Sonido de acceso incorrecto

Durante el parpadeo del LED rojo se reproduce:

```python
reproducir_tono(200, 0.12)
```

La frecuencia más baja permite distinguir claramente una contraseña incorrecta.

### Resultado

Después de esta modificación, el sistema proporciona distintos tipos de retroalimentación:

```text
Pulsación detectada
        ↓
Tono corto de 1000 Hz

Nueva captura
        ↓
Tono de 800 Hz

Clave correcta
        ↓
LED verde + tono de 1500 Hz

Clave incorrecta
        ↓
LED rojo + tono de 200 Hz
```

La prueba se realizó correctamente y los distintos sonidos pudieron diferenciarse durante el funcionamiento del prototipo.

---

## 26. Implementación de límite de tiempo por inactividad

Después de comprobar la captura, validación, LED y buzzer, se añadió una condición para cancelar una captura incompleta cuando el usuario deja de ingresar pulsaciones durante demasiado tiempo.

Se estableció un límite de:

```python
TIEMPO_LIMITE_INACTIVIDAD = 4
```

Esto significa que el usuario dispone de un máximo de cuatro segundos entre pulsaciones mientras existe una secuencia incompleta.

### Registro de la última pulsación

Se agregó la variable:

```python
tiempo_ultima_pulsacion = None
```

Cada vez que se registra una nueva pulsación, se actualiza mediante:

```python
tiempo_ultima_pulsacion = time.time()
```

`time.time()` devuelve el tiempo actual.

Posteriormente se calcula cuánto tiempo ha transcurrido:

```python
tiempo_pasado = time.time() - tiempo_ultima_pulsacion
```

### Condición de inactividad

La comprobación solamente se realiza si ya existe al menos una pulsación y todavía no se han completado las seis:

```python
if len(secuencia) > 0 and len(secuencia) < 6:
```

Después se verifica:

```python
if tiempo_pasado > TIEMPO_LIMITE_INACTIVIDAD:
```

Si han pasado más de cuatro segundos desde la última pulsación, la captura se cancela.

### Retroalimentación por timeout

Se creó:

```python
def feedback_timeout():
    GPIO.output(LED_ROJO, GPIO.HIGH)
    reproducir_tono(300, 0.3)
    GPIO.output(LED_ROJO, GPIO.LOW)
```

Cuando se supera el tiempo permitido:

- se enciende temporalmente el LED rojo;
- se reproduce un tono de 300 Hz;
- se elimina la secuencia incompleta.

El reinicio se realiza mediante:

```python
secuencia = []
tiempo_ultima_pulsacion = None
```

Además se muestra:

```text
Se excedio el limite de tiempo sin pulsaciones, se cancela la captura
```

y el sistema vuelve a esperar una nueva secuencia.

### Funcionamiento esperado

Por ejemplo:

```text
Usuario presiona botón 1
        ↓
Secuencia: [1]
        ↓
Usuario presiona botón 2
        ↓
Secuencia: [1, 2]
        ↓
Pasan más de 4 segundos
        ↓
Se cancela la captura
        ↓
LED rojo + tono de timeout
        ↓
Secuencia = []
        ↓
Sistema listo para una nueva captura
```

### Resultado de la prueba

La implementación fue probada correctamente.

Se comprobó que:

- el temporizador comienza después de una pulsación;
- cada nueva pulsación actualiza el tiempo;
- si transcurren más de cuatro segundos sin completar las seis pulsaciones, la secuencia se cancela;
- el sistema proporciona retroalimentación mediante LED y buzzer;
- después de cancelar la captura, el sistema puede iniciar una nueva secuencia sin reiniciar el programa.

---

## 27. Estado actual del prototipo de hardware

Actualmente el sistema permite:

- [x] Detectar tres botones físicos.
- [x] Identificar correctamente cuál botón fue presionado.
- [x] Asociar los botones con valores diferentes.
- [x] Capturar una secuencia de seis pulsaciones.
- [x] Controlar el rebote de los pulsadores.
- [x] Comparar la secuencia con una contraseña válida.
- [x] Mostrar si la contraseña es correcta o incorrecta.
- [x] Activar un LED verde cuando la contraseña es correcta.
- [x] Activar un LED rojo cuando la contraseña es incorrecta.
- [x] Utilizar un buzzer como indicador auditivo.
- [x] Generar diferentes tonos según el evento.
- [x] Generar un sonido al detectar una pulsación.
- [x] Generar un sonido al comenzar una nueva captura.
- [x] Generar un sonido diferente para acceso correcto.
- [x] Generar un sonido diferente para acceso incorrecto.
- [x] Reiniciar automáticamente la secuencia después de cada intento.
- [x] Cancelar una captura incompleta después de cuatro segundos de inactividad.
- [x] Permitir un nuevo intento después de un timeout.
- [x] Detectar y cancelar una captura si el buffer supera el límite máximo de seis pulsaciones.
- [x] Ejecutar el prototipo de manera continua sin problemas relevantes.

---

## 28. Flujo actual del sistema

El funcionamiento actual del prototipo puede resumirse de la siguiente manera:

```text
Iniciar programa
        ↓
Configurar botones, LED y buzzer
        ↓
Sonido de inicio
        ↓
Esperar pulsación
        ↓
¿Se presionó un botón?
        ↓ Sí
Registrar valor 1, 2 o 3
        ↓
Reproducir tono de pulsación
        ↓
Actualizar tiempo de última pulsación
        ↓
¿La secuencia supera 6 valores?
     ↓ No                     ↓ Sí
Continuar                Cancelar captura
     ↓                        ↓
¿Se completaron 6?       LED rojo + sonido
 ↓ No          ↓ Sí           ↓
¿Pasaron      Comparar     Vaciar secuencia
más de 4 s?   contraseña      ↓
 ↓             ↓          Reiniciar control
Sí / No   Correcta / Incorrecta
 ↓             ↓
Si Sí:       LED + sonido
cancelar     correspondiente
captura          ↓
 ↓          Reiniciar secuencia
LED + sonido     ↓
timeout     Esperar nueva captura
 ↓
Reiniciar secuencia
 ↓
Esperar nueva captura
```

---

## 29. Evolución del prototipo

El desarrollo del hardware siguió una evolución incremental:

```text
1 botón
   ↓
Detección básica
   ↓
Error con gpiozero/lgpio
   ↓
Cambio a RPi.GPIO
   ↓
1 botón funcionando
   ↓
3 botones funcionando
   ↓
Captura de secuencia
   ↓
Corrección de impresión repetitiva
   ↓
Validación de contraseña
   ↓
Integración de LED
   ↓
Integración de buzzer
   ↓
Sonidos diferenciados mediante PWM
   ↓
Reinicio automático
   ↓
Timeout de 4 segundos
   ↓
Prototipo funcional y estable
```

Esta evolución permite observar cómo cada cambio se incorporó y verificó de forma progresiva.

---

## 30. Conclusión actualizada

El equipo de hardware consiguió implementar y comprobar la entrada física completa del sistema de control de acceso.

Inicialmente se trabajó con un solo botón para validar la conexión GPIO y el funcionamiento del acceso desde Python.

Después de resolver el problema presentado con `gpiozero` y `lgpio`, se utilizó una implementación compatible con `RPi.GPIO`.

Posteriormente se incorporaron tres botones físicos y se comprobó que cada uno pudiera identificarse correctamente mediante un valor distinto.

Una vez validada la entrada de los tres botones, se incorporó la captura de una secuencia de seis pulsaciones y su comparación con una contraseña configurable.

También se añadieron indicadores físicos mediante un LED verde, un LED rojo y un buzzer.

El sistema utiliza distintos tonos para indicar:

- detección de una pulsación;
- inicio de captura;
- contraseña correcta;
- contraseña incorrecta;
- cancelación por tiempo de espera.

Finalmente se implementó un límite de cuatro segundos de inactividad. Si el usuario comienza una secuencia pero no completa las seis pulsaciones dentro del flujo esperado, el sistema elimina la captura parcial y vuelve automáticamente al estado inicial.

Actualmente el prototipo funciona de manera estable y permite realizar intentos consecutivos sin necesidad de reiniciar manualmente el programa.

--- 
## 31. Evidencias de validación

Durante el desarrollo se realizaron las siguientes pruebas:

- Detección independiente del botón 1.
- Detección independiente del botón 2.
- Detección independiente del botón 3.
- Captura de una secuencia de seis pulsaciones.
- Prueba con contraseña correcta.
- Prueba con contraseña incorrecta.
- Reinicio automático después de cada intento.
- Validación del LED verde para acceso correcto.
- Validación del LED rojo para acceso incorrecto.
- Validación de los distintos tonos del buzzer.
- Prueba de cancelación después de cuatro segundos de inactividad.
- Nueva captura después de una cancelación por timeout.

---

## 32. Validación del límite máximo de pulsaciones

Después de implementar la captura de seis pulsaciones y el control de inactividad, se agregó una validación adicional para evitar que el buffer de la secuencia pueda contener más pulsaciones de las permitidas.

La implementación actual trabaja con una contraseña de seis pulsaciones. Por lo tanto, se agregó la siguiente condición:

```python
if len(secuencia) > 6:
    print("Se excedió el límite de pulsaciones, se cancela la captura")
    feedback_timeout()
    secuencia = []
    tiempo_ultima_pulsacion = None
    print("Esperando que se presionen los botones...")
```

### Funcionamiento de la validación

La lista:

```python
secuencia = []
```

almacena los valores correspondientes a los botones presionados.

Normalmente, cuando la lista alcanza exactamente seis elementos, el sistema realiza la validación de la contraseña mediante:

```python
if len(secuencia) == 6:
```

Sin embargo, se incorporó una comprobación adicional:

```python
if len(secuencia) > 6:
```

Esta condición funciona como una medida de protección para evitar que, ante una situación inesperada de captura, el buffer pueda continuar almacenando valores por encima del límite establecido.

Si la cantidad de valores almacenados supera seis, el programa:

1. Detecta que se excedió el límite permitido.
2. Muestra el mensaje:

```text
Se excedió el límite de pulsaciones, se cancela la captura
```

3. Activa la retroalimentación de error mediante:

```python
feedback_timeout()
```

4. Vacía la secuencia mediante:

```python
secuencia = []
```

5. Reinicia el control de tiempo:

```python
tiempo_ultima_pulsacion = None
```

6. Regresa al estado de espera para comenzar una nueva captura.

### Flujo de la validación

```text
Registrar pulsación
        ↓
Agregar valor a secuencia
        ↓
Comprobar cantidad de valores
        ↓
¿len(secuencia) > 6?
     ↓ No               ↓ Sí
Continuar          Cancelar captura
     ↓                  ↓
¿len(secuencia) == 6?   LED rojo + sonido
     ↓                  ↓
Validar contraseña      Vaciar secuencia
                        ↓
                 Reiniciar temporizador
                        ↓
                 Esperar nueva captura
```

### Objetivo de esta protección

La validación permite mantener controlado el tamaño de la secuencia utilizada por el sistema.

La contraseña configurada actualmente utiliza seis pulsaciones, por lo que cualquier estado en el que el buffer supere esta cantidad se considera inválido y provoca el reinicio de la captura.

Esta comprobación complementa las otras condiciones de reinicio ya implementadas:

- reinicio después de una contraseña correcta;
- reinicio después de una contraseña incorrecta;
- reinicio después de superar cuatro segundos de inactividad;
- reinicio si el buffer supera el máximo de seis pulsaciones.

### Resultado

Con esta modificación se añadió una medida adicional de control sobre la captura.

El sistema mantiene como funcionamiento normal la evaluación al completar seis pulsaciones, pero también cuenta con una protección para cancelar la captura si, por alguna condición inesperada, el buffer llega a superar este límite.