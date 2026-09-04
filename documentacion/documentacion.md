# Documentación del equipo de hardware

## Proyecto Integrativo 1

### Control de acceso local con Raspberry Pi

---

## 1. Objetivo del equipo de hardware

El equipo de hardware tiene como objetivo implementar la parte física del sistema de control de acceso mediante botones conectados a una Raspberry Pi 5.

Cada botón representará un valor diferente que posteriormente será utilizado por el programa para formar una secuencia de acceso.

La función principal del equipo de hardware es conseguir que las pulsaciones físicas realizadas por el usuario puedan ser detectadas correctamente por la Raspberry Pi y posteriormente enviadas al programa desarrollado por el equipo de software.

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
- [ ] Incorporar el segundo botón.
- [ ] Incorporar el tercer botón.
- [ ] Realizar la integración con el programa principal.

---

## 17. Próximo objetivo de hardware

El siguiente objetivo inmediato es comprobar que la nueva versión del programa detecte correctamente la pulsación del primer botón.

El resultado esperado en terminal es:

```text
Programa iniciado
Esperando que presiones el botón...

BOTÓN PRESIONADO
Botón liberado
```

Cada vez que el usuario vuelva a presionar el botón deberá repetirse:

```text
BOTÓN PRESIONADO
Botón liberado
```

Una vez comprobado este comportamiento, se podrá continuar con los otros dos botones.

---

## 18. Configuración prevista para los tres botones

Después de comprobar el funcionamiento del primer pulsador se realizará la conexión de tres botones.

De momento, la configuración prevista es:

| Botón | Valor | GPIO BCM | Pin físico |
|---|---:|---:|---:|
| Botón 1 | 1 | GPIO18 | 12 |
| Botón 2 | 2 | Por definir | Por definir |
| Botón 3 | 3 | Por definir | Por definir |
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

El trabajo desarrollado por el equipo de hardware está principalmente relacionado con los siguientes requerimientos.

### RF-01

> El sistema deberá capturar la secuencia introducida, compararla con una clave válida y determinar si el acceso se autoriza o se rechaza.

El equipo de hardware proporciona los dispositivos físicos mediante los cuales el usuario introducirá la secuencia.

### RF-02

> El sistema capturará una clave de 4 a 6 pulsaciones.

Los botones permitirán generar las pulsaciones necesarias para formar la clave.

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
Pendiente: confirmar lectura física
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

El siguiente paso consiste en comprobar físicamente el funcionamiento de esta segunda implementación.

Una vez que el primer botón sea detectado correctamente, se agregarán los otros dos pulsadores y posteriormente se integrará la entrada física con el programa principal del sistema de control de acceso.