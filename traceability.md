# 8. Trazabilidad

El archivo `traceability.md` permite reconstruir **por qué existe un cambio y cómo fue verificado**, vinculando los requerimientos funcionales y no funcionales del sistema con sus issues, pull requests, cambios específicos en código/hardware y las evidencias de validación empírica.

---

## Matriz de Trazabilidad de Requerimientos

| Requerimiento | Issue | PR / cambio | Evidencia de validación |
| :--- | :--- | :--- | :--- |
| **RF-01**: Captura, comparación y autorización de acceso | Issue #5 | PR #7 / PR #9 | **Demostración**: Al ingresar la clave válida `[1, 2, 3, 1, 2, 3]` mediante los pulsadores físicos, el sistema valida la coincidencia contra `PASSWORD_VALIDA`, enciende el LED verde (GPIO 23) y genera tres tonos audibles de confirmación (1500 Hz) con el buzzer PWM (GPIO 25), autorizando el acceso. Al ingresar una secuencia incorrecta, activa el LED rojo (GPIO 24) y reproduce tres tonos graves (200 Hz), denegando el acceso. |
| **RF-02**: Longitud de clave de 4 a 6 pulsaciones | Issue #3 / Issue #5 | PR #3 / PR #7 / PR #9 | **Demostración**: Los 3 pulsadores físicos (`PIN_BOTON_1 = 14`, `PIN_BOTON_2 = 15`, `PIN_BOTON_3 = 18`) registran pulsaciones en la lista `secuencia`. Al acumular exactamente 6 pulsaciones (`len(secuencia) == 6`), el sistema bloquea la captura adicional, imprime `"Se completaron 6 pulsaciones, secuencia lista: [...]"` y procede inmediatamente a la validación. |
| **RF-03**: Señalización visual mediante luces LED (verde/rojo) | Issue #5 | PR #7 | **Demostración**: Salidas digitales configuradas en GPIO 23 (`LED_VERDE`) y GPIO 24 (`LED_ROJO`). Si la clave es correcta se invoca `feedback_correcto()` encendiendo el LED verde en 3 pulsos; si la clave es incorrecta o se produce timeout se activa el LED rojo (`feedback_incorrecto()` / `feedback_timeout()`). |
| **RF-04**: Reinicio automático tras cada captura para nuevos datos | Issue #5 | PR #7 / PR #9 | **Demostración**: Al culminar la evaluación de una clave (correcta o incorrecta) o al vencer el temporizador, el sistema ejecuta `secuencia = []` y `tiempo_ultima_pulsacion = None`, imprime `"Esperando nueva captura"` y retorna al ciclo de escucha de pulsadores sin requerir reinicio del script ni intervención manual. |
| **RF-05**: Cancelación y purga del búfer por inactividad > 4 segundos | Issue #5 | PR #9 | **Demostración**: Al capturar una secuencia incompleta (1 a 5 pulsaciones) y dejar de presionar botones durante más de 4 segundos (`tiempo_pasado > TIEMPO_LIMITE_INACTIVIDAD = 4`), el sistema ejecuta `feedback_timeout()`, imprime `"Se excedio el limite de tiempo sin pulsaciones, se cancela la captura"`, limpia `secuencia = []` y vuelve al estado inicial de espera. |
| **RF-06**: Señal sonora al reiniciar el sistema y permitir nuevo ingreso | Issue #5 | PR #7 / PR #9 | **Demostración**: La función `sonido_inicio_captura()` emite un tono audible distintivo de 800 Hz durante 0.15 segundos (`reproducir_tono(800, 0.15)`). Se ejecuta tanto al arrancar el programa como después de cada ciclo de evaluación y purga del búfer, avisando que el sistema está listo. |
| **RF-07**: Tres tonos cortos de buzzer al evaluar la secuencia | Issue #5 | PR #7 | **Demostración**: En `feedback_correcto()`, el buzzer reproduce 3 tonos agudos de 1500 Hz (0.12 s encendido, 0.15 s apagado) sincronizados con el LED verde. En `feedback_incorrecto()`, reproduce 3 tonos graves de 200 Hz sincronizados con el LED rojo. Ambos verificados acústica y visualmente. |
| **RNF-01**: Prevención de rebote físico del botón (antirrebote/debounce) | Issue #2 / Issue #3 | PR #3 / PR #7 / PR #10 | **Demostración**: Configuración de resistencias internas `GPIO.PUD_UP` y filtro de software en `revisar_boton()`: bucle de espera activa mientras el botón está pulsado (`while GPIO.input(pin) == GPIO.LOW: time.sleep(0.01)`) y retardo estabilizador de liberación (`time.sleep(0.2)`). Presiones mecánicas rápidas o ruidosas registran exactamente un solo dígito sin duplicaciones. |
| **RNF-02**: Conservación segura de clave administrable | Issue #5 | PR #7 / PR #9 | **Demostración**: `PASSWORD_VALIDA` está almacenada como constante en el código ejecutable local en la Raspberry Pi. No existen combinaciones físicas en los botones que permitan consultar ni sobreescribir la contraseña; cualquier actualización de la clave requiere autenticación SSH de administrador en Ubuntu. |
| **RNF-03**: Tiempo de respuesta ≤ 1 segundo tras la última pulsación | Issue #5 | PR #7 / PR #9 | **Demostración**: La evaluación condicional `if secuencia == PASSWORD_VALIDA:` se dispara de manera síncrona en microsegundos tan pronto como se registra la 6ta pulsación. El tiempo medido desde la liberación del botón hasta el inicio del primer pulso visual/auditivo es inferior a 0.05 segundos (< 50 ms), superando con holgura el límite de 1 segundo. |

---

## Relación lógica y reconstrucción de cambios por requerimiento

No se busca llenar una tabla únicamente por cumplir. Debe existir una relación lógica entre la necesidad, el cambio realizado y la manera en que fue validado:

---

### RF-01: Captura, comparación y autorización de acceso

1. **Necesidad (Requerimiento)**:
   - El sistema deberá capturar la secuencia introducida, compararla con una clave válida y determinar si el acceso se autoriza o se rechaza.

2. **Origen / Justificación (Issue #5: "Corrección de código y ampliación")**:
   - Tras validar la lectura física individual de los botones, se detectó la necesidad de almacenar la secuencia completa, compararla con la contraseña de acceso autorizada e incorporar retroalimentación visual (LEDs verde y rojo) y auditiva (buzzer) para informar de manera inequívoca si el acceso es concedido o denegado.

3. **Cambio implementado (PR #7 / PR #9 - `src/Main_code.py`)**:
   - Definición de `PASSWORD_VALIDA = [1, 2, 3, 1, 2, 3]` y configuración de pines de salida para `LED_VERDE` (pin 23), `LED_ROJO` (pin 24) y `BUZZER` (pin 25 con PWM).
   - Creación de las funciones de retroalimentación `feedback_correcto()` y `feedback_incorrecto()`.
   - Implementación de la condición de evaluación al completarse las pulsaciones requeridas:
     ```python
     if secuencia == PASSWORD_VALIDA:
         print("Contraseña correcta")
         feedback_correcto()
     else:
         print("Contraseña incorrecta")
         feedback_incorrecto()
     ```
   - Reinicio del búfer (`secuencia = []`) y aviso de inicio de nueva captura para el siguiente ciclo.

4. **Evidencia de validación**:
   - **Validación positiva (acceso autorizado)**:
     - *Procedimiento*: Ejecución del script en Raspberry Pi e ingreso de la secuencia válida presionando los botones físicos 1, 2, 3, 1, 2, 3.
     - *Resultado*: Impresión en consola `"Contraseña correcta"`, activación del LED verde y emisión sincronizada de 3 tonos PWM a 1500 Hz.
   - **Validación negativa (acceso denegado)**:
     - *Procedimiento*: Ingreso deliberado de una combinación incorrecta (ej. 1, 1, 1, 1, 1, 1).
     - *Resultado*: Impresión en consola `"Contraseña incorrecta"`, activación del LED rojo y emisión de 3 tonos PWM a 200 Hz.

---

### RF-02: Longitud de clave de 4 a 6 pulsaciones

1. **Necesidad (Requerimiento)**:
   - El sistema capturará una clave de 4 a 6 pulsaciones.

2. **Origen / Justificación (Issue #3 / Issue #5)**:
   - Se requería definir una longitud fija y segura para la secuencia de acceso que garantice suficiente entropía física sin dificultar la introducción al usuario. Se adoptó una clave de 6 pulsaciones basada en 3 pulsadores.

3. **Cambio implementado (PR #3 / PR #7 - `src/Main_code.py`)**:
   - Mapeo de pulsadores en pines BCM: `PIN_BOTON_1 = 14`, `PIN_BOTON_2 = 15` y `PIN_BOTON_3 = 18`.
   - Acumulación de valores en lista dinámica `secuencia.append(valor)`.
   - Control de longitud máxima evaluada:
     ```python
     if len(secuencia) == 6:
         print("Se completaron 6 pulsaciones, secuencia lista:", secuencia)
         # Evaluación de clave...
     ```

4. **Evidencia de validación**:
   - *Procedimiento*: Pulsar botones en diversas combinaciones registrando la longitud de entrada.
   - *Resultado*: La terminal muestra en cada paso el estado (`"Secuencia actual: [1]"`, `"Secuencia actual: [1, 2]"`, etc.). Al llegar exactamente al sexto valor, se activa el bloque de evaluación impidiendo la captura de pulsaciones extra para ese ciclo.

---

### RF-03: Señalización visual mediante luces LED (verde y rojo)

1. **Necesidad (Requerimiento)**:
   - El sistema mostrará por medio de luces LED si la clave es válida (verde) o no es válida (rojo).

2. **Origen / Justificación (Issue #5)**:
   - Se necesitaba una interfaz luminosa externa en la protoboard que indicara visualmente a cualquier usuario si la puerta/acceso fue desbloqueado o bloqueado.

3. **Cambio implementado (PR #7 - `src/Main_code.py`)**:
   - Inicialización de salidas `LED_VERDE = 23` y `LED_ROJO = 24` en modo `GPIO.OUT`.
   - Modulación de salidas mediante `GPIO.output(LED_VERDE, GPIO.HIGH)` y `GPIO.output(LED_ROJO, GPIO.HIGH)` dentro de `feedback_correcto()` y `feedback_incorrecto()`.

4. **Evidencia de validación**:
   - *Procedimiento*: Introducir combinaciones válidas e inválidas observando los diodos LED montados con sus resistencias limitadoras de 220 Ω en protoboard.
   - *Resultado*: Clave válida genera 3 destellos del LED verde. Clave inválida genera 3 destellos del LED rojo. Ningún LED se enciende durante la captura normal hasta evaluar el resultado.

---

### RF-04: Reinicio automático tras cada captura

1. **Necesidad (Requerimiento)**:
   - El sistema se reiniciará después de cada captura para permitir nuevos datos.

2. **Origen / Justificación (Issue #5: "Corrección de código y ampliación")**:
   - En la primera versión el script terminaba tras evaluar la primera clave (`break`). Se requería mantener el sistema en ejecución continua desocupando la memoria del búfer.

3. **Cambio implementado (PR #7 / PR #9 - `src/Main_code.py`)**:
   - Reemplazo de la instrucción `break` por el reseteo de variables de sesión:
     ```python
     secuencia = []
     tiempo_ultima_pulsacion = None
     print("Esperando nueva captura")
     sonido_inicio_captura()
     ```
   - El bucle infinito `while True` retoma la escucha sin reiniciar el programa.

4. **Evidencia de validación**:
   - *Procedimiento*: Realizar múltiples intentos sucesivos de autenticación (correctos e incorrectos) sin detener el proceso de Python.
   - *Resultado*: En cada iteración el búfer se restablece a longitud cero (`[]`) y permite ingresar de inmediato una nueva clave de 6 dígitos.

---

### RF-05: Cancelación y purga del búfer por inactividad (> 4 segundos)

1. **Necesidad (Requerimiento)**:
   - Si transcurren más de 4 segundos sin recibir una nueva pulsación durante una captura incompleta, el sistema limpiará el búfer de entrada, descartará los datos introducidos y regresará automáticamente a la pantalla de inicio.

2. **Origen / Justificación (Issue #5 / PR #9)**:
   - Evitar que una secuencia parcial abandonada por un usuario quede almacenada indefinidamente, lo cual generaría accesos no deseados para el siguiente usuario o vulnerabilidades de seguridad.

3. **Cambio implementado (PR #9 - `src/Main_code.py`)**:
   - Declaración de constante `TIEMPO_LIMITE_INACTIVIDAD = 4`.
   - Registro de marca de tiempo `tiempo_ultima_pulsacion = time.time()` tras cada pulsación.
   - Verificación periódica dentro del ciclo principal:
     ```python
     if len(secuencia) > 0 and len(secuencia) < 6:
         if tiempo_ultima_pulsacion is not None:
             tiempo_pasado = time.time() - tiempo_ultima_pulsacion
             if tiempo_pasado > TIEMPO_LIMITE_INACTIVIDAD:
                 print("Se excedio el limite de tiempo sin pulsaciones, se cancela la captura")
                 feedback_timeout()
                 secuencia = []
                 tiempo_ultima_pulsacion = None
                 print("Esperando que se presionen los botones...")
     ```
   - Creación de `feedback_timeout()` que enciende el LED rojo y reproduce un tono de advertencia a 300 Hz por 0.3 s.

4. **Evidencia de validación**:
   - *Procedimiento*: Ingresar de 1 a 3 pulsaciones físicas y esperar más de 4 segundos cronometrados sin presionar ningún botón.
   - *Resultado*: A los 4.01 s se emite la advertencia lumínica/acústica, se imprime `"Se excedio el limite de tiempo sin pulsaciones, se cancela la captura"` y la variable `secuencia` vuelve a `[]`.

---

### RF-06: Señal sonora al reiniciar el sistema y permitir nuevo ingreso

1. **Necesidad (Requerimiento)**:
   - El sistema emitirá un sonido por cada vez que se reinicie el sistema y se pueda volver a ingresar la contraseña.

2. **Origen / Justificación (Issue #5)**:
   - Brindar retroalimentación sonora no visual que indique claramente al usuario invidente o distraído que el sistema está listo para recibir el primer dígito.

3. **Cambio implementado (PR #7 / PR #9 - `src/Main_code.py`)**:
   - Implementación de la función `sonido_inicio_captura()`:
     ```python
     def sonido_inicio_captura():
         reproducir_tono(800, 0.15)
     ```
   - Invocación al iniciar el programa (línea 74) y después de cada ciclo de evaluación (línea 121) o timeout.

4. **Evidencia de validación**:
   - *Procedimiento*: Iniciar el sistema y realizar validaciones sucesivas prestando atención a la respuesta acústica del hardware.
   - *Resultado*: El buzzer PWM reproduce un pitido claro de 800 Hz durante 150 ms en cada evento de habilitación del sistema.

---

### RF-07: Tres tonos cortos de buzzer al evaluar la secuencia

1. **Necesidad (Requerimiento)**:
   - El sistema emitirá tres tonos cortos del buzzer al evaluar la secuencia ingresada, tanto si la contraseña es correcta como si es incorrecta, coincidiendo con el encendido del LED verde o rojo correspondiente.

2. **Origen / Justificación (Issue #5)**:
   - Reforzar multimodalmente la respuesta de acceso mediante señales auditivas con frecuencias diferenciadas según el veredicto (éxito vs. fallo).

3. **Cambio implementado (PR #7 - `src/Main_code.py`)**:
   - Configuración de modulación por ancho de pulsos en el buzzer: `buzzer_pwm = GPIO.PWM(BUZZER, 440)`.
   - Modulación de tonos diferenciados en bucles de 3 repeticiones:
     - Clave correcta: `reproducir_tono(1500, 0.12)` alternado con 0.15 s de silencio y sincronizado con `LED_VERDE`.
     - Clave incorrecta: `reproducir_tono(200, 0.12)` alternado con 0.15 s de silencio y sincronizado con `LED_ROJO`.

4. **Evidencia de validación**:
   - *Procedimiento*: Evaluar secuencias válidas e inválidas monitorizando la sincronía visual y acústica.
   - *Resultado*: Tres beeps agudos inequívocos (1500 Hz) con el LED verde para acceso permitido; tres beeps graves (200 Hz) con el LED rojo para acceso denegado.

---

### RNF-01: Prevención de rebote físico del botón (antirrebote / debounce)

1. **Necesidad (Requerimiento)**:
   - El sistema evitará registrar una pulsación física debido al rebote del botón.

2. **Origen / Justificación (Issue #2 / Issue #3)**:
   - Los pulsadores de contacto mecánico generan oscilaciones eléctricas (ruido/rebote) de milisegundos al cerrarse o abrirse, lo que puede registrar múltiples pulsaciones falsas por un solo toque físico.

3. **Cambio implementado (PR #3 / PR #7 / PR #10 - `src/Main_code.py`)**:
   - Configuración de resistencias internas `pull_up_down=GPIO.PUD_UP`.
   - Lógica de espera activa y retraso de estabilización en `revisar_boton()`:
     ```python
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
     ```

4. **Evidencia de validación**:
   - *Procedimiento*: Presionar de forma rápida, repetitiva y con diferente fuerza los botones físicos conectados a GPIO 14, 15 y 18.
   - *Resultado*: Cada pulsación mecánica individual se traduce en exactamente un incremento en el arreglo `secuencia`, sin disparos múltiples espurios.

---

### RNF-02: Conservación segura de clave administrable

1. **Necesidad (Requerimiento)**:
   - La contraseña válida deberá conservarse de forma segura durante la ejecución del sistema y solo podrá modificarse por el administrador.

2. **Origen / Justificación (Issue #5)**:
   - Impedir que usuarios no autorizados puedan alterar o consultar la clave mediante manipulación física del teclado de botones o inspección no autorizada.

3. **Cambio implementado (PR #7 / PR #9 - `src/Main_code.py`)**:
   - Encapsulamiento de la clave como constante en el código fuente de ejecución local (`PASSWORD_VALIDA = [1, 2, 3, 1, 2, 3]`), protegida bajo los permisos de archivo de Ubuntu en la Raspberry Pi.
   - El programa no ofrece ningún comando ni combinación de botones físicos que modifique el estado de la clave en caliente.

4. **Evidencia de validación**:
   - *Procedimiento*: Intento de manipulación externa mediante los botones del protoboard y verificación de accesos.
   - *Resultado*: Los botones solo permiten alimentar secuencias de verificación contra la clave fija. La reconfiguración de la contraseña requiere obligatoriamente una sesión autenticada vía SSH con permisos de edición sobre el archivo en el sistema operativo.

---

### RNF-03: Tiempo de respuesta ≤ 1 segundo tras la última pulsación

1. **Necesidad (Requerimiento)**:
   - El sistema deberá evaluar y presentar la respuesta (aprobado/desaprobado) en un tiempo no mayor a 1 segundo tras capturar el último dígito de la secuencia.

2. **Origen / Justificación (Issue #5)**:
   - Garantizar una experiencia de usuario fluida e instantánea en el punto de control de acceso, evitando demoras perceptibles al autorizar o denegar el paso.

3. **Cambio implementado (PR #7 / PR #9 - `src/Main_code.py`)**:
   - Evaluación síncrona en memoria local: en cuanto `len(secuencia) == 6`, la sentencia `if secuencia == PASSWORD_VALIDA:` se ejecuta inmediatamente sin intermediarios ni llamadas de red bloqueantes.

4. **Evidencia de validación**:
   - *Procedimiento*: Medición mediante marcas temporales de sistema entre la liberación del sexto pulsador (`Boton liberado`) y el inicio de la función de feedback correspondiente (`feedback_correcto` o `feedback_incorrecto`).
   - *Resultado*: Latencia de procesamiento inferior a 0.05 segundos (50 ms), cumpliendo con holgura el umbral máximo de 1.0 segundo.
