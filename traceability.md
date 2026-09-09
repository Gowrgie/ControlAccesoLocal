# 8. Trazabilidad

El archivo `traceability.md` permite reconstruir **por qué existe un cambio y cómo fue verificado**, vinculando los requerimientos funcionales y no funcionales del sistema con sus issues, pull requests, cambios específicos en código/hardware y las evidencias de validación empírica.

---

## Matriz de Trazabilidad de Requerimientos

| Requisito | Issue / Origen | PR / Cambio | Estado actual | Evidencia de validación |
| :--- | :--- | :--- | :--- | :--- |
| **RF-01**: Captura, comparación y autorización de acceso | Issue #5 | PR #3 + PR #7 | Cumple | **Demostración**: Los 3 pulsadores físicos capturan la secuencia (PR #3) y el sistema la valida contra `PASSWORD_VALIDA` (PR #7). Al ingresar la clave válida `[1, 2, 3, 1, 2, 3]`, enciende el LED verde (GPIO 23) y emite 3 tonos de 1500 Hz en el buzzer PWM (GPIO 25). Si es incorrecta, activa el LED rojo (GPIO 24) y 3 tonos de 200 Hz. |
| **RF-02**: Longitud de clave de 6 pulsaciones | Issue #3 / Issue #5 | PR #3 | Cumple (evalúa 6 pulsaciones) | **Demostración**: Pulsadores en GPIO 14, 15 y 18 registran pulsaciones en la lista `secuencia`. Al acumular exactamente 6 pulsaciones (`len(secuencia) == 6`), el sistema bloquea capturas adicionales, imprime el contenido de la secuencia y procede de inmediato a la evaluación. |
| **RF-03**: Señalización visual mediante luces LED (verde/rojo) | Issue #1 + Issue #5 | PR #7 | Cumple | **Demostración**: Salidas digitales en GPIO 23 (`LED_VERDE`) y GPIO 24 (`LED_ROJO`). Ante clave correcta, `feedback_correcto()` parpadea 3 veces en verde; ante clave errónea o timeout, `feedback_incorrecto()` / `feedback_timeout()` activan el LED rojo. |
| **RF-04**: Reinicio automático tras cada captura para nuevos datos | Sin Issue específico | PR #7 + PR #9 | Cumple | **Demostración**: Al concluir la evaluación de la clave (`feedback_correcto`/`feedback_incorrecto` en PR #7) o al cancelarse por timeout (PR #9), se ejecuta `secuencia = []` y `tiempo_ultima_pulsacion = None`, imprimiendo `"Esperando nueva captura"` para reiniciar el ciclo en caliente sin reiniciar el script. |
| **RF-05**: Cancelación y purga del búfer por inactividad > 4 segundos | Issue #1 | PR #9 | Cumple | **Demostración**: Si transcurren más de 4 segundos sin pulsar botones durante una captura incompleta (1 a 5 pulsaciones), el sistema activa `feedback_timeout()` (LED rojo + tono 300 Hz), muestra mensaje de cancelación, limpia `secuencia = []` y regresa al inicio. |
| **RF-06**: Señal sonora al reiniciar el sistema y permitir nuevo ingreso | Issue #5 | PR #7 | Cumple | **Demostración**: `sonido_inicio_captura()` reproduce un tono de 800 Hz durante 0.15 s en el buzzer (GPIO 25). Se ejecuta al arrancar el programa y tras culminar cada ciclo de evaluación o purga por inactividad. |
| **RF-07**: Tres tonos cortos de buzzer al evaluar la secuencia | Issue #5 | PR #7 | Cumple | **Demostración**: En `feedback_correcto()`, el buzzer reproduce 3 tonos agudos de 1500 Hz sincronizados con el LED verde. En `feedback_incorrecto()`, reproduce 3 tonos graves de 200 Hz sincronizados con el LED rojo. |
| **RNF-01**: Prevención de rebote físico del botón (antirrebote / debounce) | Sin Issue específico | PR #3 | Cumple | **Demostración**: Configuración con resistencias internas `GPIO.PUD_UP` y lógica en `revisar_boton()`: bucle de espera mientras el botón está presionado (`while GPIO.input(pin) == GPIO.LOW: time.sleep(0.01)`) y retraso estabilizador de `time.sleep(0.2)`. Cada pulsación física produce un solo registro. |
| **RNF-02**: Conservación segura de clave administrable | Issue #1 | PR #11 | Cumple | **Demostración**: Almacenamiento seguro de la clave con hash SHA-256 en archivo persistente `password.txt` y modificación exclusiva por administrador mediante `--admin`. La entrada de nueva clave se realiza con dígitos continuos sin espacios (ej. `123123`), convertidos individualmente a enteros para coincidir con la secuencia capturada por los pulsadores físicos. |
| **RNF-03**: Tiempo de respuesta ≤ 1 segundo tras la última pulsación | Issue #1 | PR #7 / prueba de tiempo | Pendiente de evidencia formal | **Demostración**: La evaluación se dispara en memoria local en cuanto `len(secuencia) == 6`, iniciando el feedback de forma inmediata (< 0.1 s). Se encuentra pendiente instrumentar la medición cronométrica formal con `time.perf_counter()` para asentar la evidencia cuantitativa en el repositorio. |

---

## Relación lógica y reconstrucción de cambios por requerimiento

A continuación se detalla la justificación técnica, el historial de cambios y la validación empírica para cada requerimiento:

---

### RF-01: Captura, comparación y autorización de acceso

1. **Necesidad (Requerimiento)**:
   - El sistema deberá capturar la secuencia introducida, compararla con una clave válida y determinar si el acceso se autoriza o se rechaza.

2. **Origen / Justificación (Issue #5: "Corrección de código y ampliación")**:
   - Tras disponer de la lectura física inicial de los tres botones (incorporada en PR #3), se requería almacenar la secuencia completa, compararla contra la contraseña autorizada e integrar indicadores luminosos (LEDs verde y rojo) y audibles (buzzer) para reflejar la decisión de acceso de manera inequívoca.

3. **Cambio implementado (PR #3 + PR #7 - `src/Main_code.py`)**:
   - **PR #3**: Habilitó los 3 pulsadores físicos y la acumulación dinámica en la lista `secuencia`.
   - **PR #7**: Estableció la clave de referencia `PASSWORD_VALIDA = [1, 2, 3, 1, 2, 3]`, configuró salidas en `LED_VERDE` (pin 23), `LED_ROJO` (pin 24) y `BUZZER` (pin 25 PWM), e implementó la evaluación condicional:
     ```python
     if secuencia == PASSWORD_VALIDA:
         print("Contraseña correcta")
         feedback_correcto()
     else:
         print("Contraseña incorrecta")
         feedback_incorrecto()
     ```
   - *Evolución*: Con la integración de PR #11 a `main`, esta comprobación se realiza mediante `if verificar_password(secuencia):`, comparando el hash SHA-256 de la secuencia contra el hash almacenado en el archivo persistente `password.txt`.

4. **Evidencia de validación**:
   - **Validación positiva (acceso autorizado)**:
     - *Procedimiento*: Ingreso de la secuencia válida presionando los botones físicos 1, 2, 3, 1, 2, 3.
     - *Resultado*: Impresión en consola `"Contraseña correcta"`, activación del LED verde y emisión sincronizada de 3 tonos PWM a 1500 Hz.
   - **Validación negativa (acceso denegado)**:
     - *Procedimiento*: Ingreso de una combinación incorrecta (ej. 1, 1, 1, 1, 1, 1).
     - *Resultado*: Impresión en consola `"Contraseña incorrecta"`, activación del LED rojo y emisión de 3 tonos PWM a 200 Hz.

---

### RF-02: Longitud de clave de 6 pulsaciones

1. **Necesidad (Requerimiento)**:
   - El sistema capturará una clave de 6 pulsaciones fijas (alineado a la implementación física del prototipo).

2. **Origen / Justificación (Issue #3 / Issue #5)**:
   - Se requería delimitar la longitud de la secuencia de acceso para brindar suficiente entropía física sin complicar la interacción del usuario sobre el protoboard de 3 botones.

3. **Cambio implementado (PR #3 - `src/Main_code.py`)**:
   - Mapeo de pulsadores en pines BCM: `PIN_BOTON_1 = 14`, `PIN_BOTON_2 = 15` y `PIN_BOTON_3 = 18`.
   - Acumulación de valores mediante `secuencia.append(valor)`.
   - Control de longitud evaluada:
     ```python
     if len(secuencia) == 6:
         print("Se completaron 6 pulsaciones, secuencia lista:", secuencia)
         # Disparo de la validación
     ```
   - *Alineación técnica*: Aunque el documento original `Requirements.md` enunciaba de 4 a 6 pulsaciones, la lógica implementada en hardware evalúa de forma determinista y estricta al completar exactamente 6 pulsaciones, tal como documenta PR #3.

4. **Evidencia de validación**:
   - *Procedimiento*: Pulsar botones registrando la longitud de entrada en consola.
   - *Resultado*: La terminal muestra paso a paso `"Secuencia actual: [1]"`, `"Secuencia actual: [1, 2]"`, etc. Al registrar el sexto elemento, se bloquea la captura adicional y se procede a la validación.

---

### RF-03: Señalización visual mediante luces LED (verde y rojo)

1. **Necesidad (Requerimiento)**:
   - El sistema mostrará por medio de luces LED si la clave es válida (verde) o no es válida (rojo).

2. **Origen / Justificación (Issue #1 + Issue #5)**:
   - Issue #1 estipuló que el LED verde señaliza clave válida y el rojo clave inválida. Issue #5 formalizó la conexión física de ambos diodos en la protoboard.

3. **Cambio implementado (PR #7 - `src/Main_code.py`)**:
   - Declaración de salidas digitales `LED_VERDE = 23` y `LED_ROJO = 24`.
   - Modulación de salidas mediante `feedback_correcto()` (3 destellos en verde) y `feedback_incorrecto()` / `feedback_timeout()` (activación en rojo).

4. **Evidencia de validación**:
   - *Procedimiento*: Introducir secuencias válidas e inválidas observando los LEDs conectados con resistencias limitadoras de 220 Ω.
   - *Resultado*: Clave válida genera 3 destellos del LED verde. Clave inválida o timeout activan el LED rojo.

---

### RF-04: Reinicio automático tras cada captura para nuevos datos

1. **Necesidad (Requerimiento)**:
   - El sistema se reiniciará después de cada captura para permitir nuevos datos.

2. **Origen / Justificación (Sin Issue específico)**:
   - Mantener el prototipo en ejecución continua dentro de un bucle `while True`, limpiando el búfer de memoria tras cada intento sin requerir reiniciar manualmente el proceso.

3. **Cambio implementado (PR #7 + PR #9 - `src/Main_code.py`)**:
   - **PR #7**: Reemplazó la terminación del script (`break`) por la purga de variables al finalizar la evaluación:
     ```python
     secuencia = []
     tiempo_ultima_pulsacion = None
     print("Esperando nueva captura")
     sonido_inicio_captura()
     ```
   - **PR #9**: Agregó la misma purga automática en caso de expirar el temporizador de inactividad.

4. **Evidencia de validación**:
   - *Procedimiento*: Ejecutar múltiples intentos consecutivos (aciertos, fallos y pausas) sin reiniciar el script de Python.
   - *Resultado*: En todos los casos el búfer vuelve a `[]` y el sistema queda receptivo para una nueva clave.

---

### RF-05: Cancelación y purga del búfer por inactividad (> 4 segundos)

1. **Necesidad (Requerimiento)**:
   - Si transcurren más de 4 segundos sin recibir una nueva pulsación durante una captura incompleta, el sistema limpiará el búfer de entrada, descartará los datos introducidos y regresará automáticamente al estado de espera inicial.

2. **Origen / Justificación (Issue #1)**:
   - Issue #1 definió el requisito de seguridad para evitar que secuencias parciales abandonadas por un usuario queden en memoria indefinidamente. Fue implementado de forma específica en **PR #9** ("agrega timeout de 4 segundos por inactividad (RF-05)").

3. **Cambio implementado (PR #9 - `src/Main_code.py`)**:
   - Definición de constante `TIEMPO_LIMITE_INACTIVIDAD = 4`.
   - Control temporal en el bucle principal:
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
   - Función `feedback_timeout()` que enciende el LED rojo y emite un tono de advertencia a 300 Hz durante 0.3 s.

4. **Evidencia de validación**:
   - *Procedimiento*: Ingresar entre 1 y 3 pulsaciones y esperar más de 4 segundos sin tocar botones.
   - *Resultado*: A los 4 segundos transcurridos, el sistema emite el aviso sonoro/lumínico, imprime el mensaje de cancelación y restablece `secuencia = []`.

---

### RF-06: Señal sonora al reiniciar el sistema y permitir nuevo ingreso

1. **Necesidad (Requerimiento)**:
   - El sistema emitirá un sonido por cada vez que se reinicie el sistema y se pueda volver a ingresar la contraseña.

2. **Origen / Justificación (Issue #5)**:
   - Ofrecer una indicación acústica que informe al usuario que el sistema está preparado para recibir el primer dígito.

3. **Cambio implementado (PR #7 - `src/Main_code.py`)**:
   - Creación de la función `sonido_inicio_captura()`:
     ```python
     def sonido_inicio_captura():
         reproducir_tono(800, 0.15)
     ```
   - Invocación al arrancar el programa y tras concluir la evaluación de cada clave (mantenida también en PR #9 tras cancelaciones).

4. **Evidencia de validación**:
   - *Procedimiento*: Escuchar la respuesta física del buzzer al inicio y entre ciclos consecutivos.
   - *Resultado*: El buzzer PWM genera un pitido claro de 800 Hz durante 150 ms en cada puesta a punto del sistema.

---

### RF-07: Tres tonos cortos de buzzer al evaluar la secuencia

1. **Necesidad (Requerimiento)**:
   - El sistema emitirá tres tonos cortos del buzzer al evaluar la secuencia ingresada, tanto si la contraseña es correcta como si es incorrecta, coincidiendo con el encendido del LED verde o rojo correspondiente.

2. **Origen / Justificación (Issue #5)**:
   - Refuerzo auditivo con frecuencias diferenciadas para indicar de forma inequívoca el veredicto de acceso.

3. **Cambio implementado (PR #7 - `src/Main_code.py`)**:
   - Configuración de modulación PWM: `buzzer_pwm = GPIO.PWM(BUZZER, 440)`.
   - Tonos diferenciados en ráfagas de 3 pulsos:
     - Clave válida: `reproducir_tono(1500, 0.12)` alternado con 0.15 s de silencio, sincronizado con `LED_VERDE`.
     - Clave errónea: `reproducir_tono(200, 0.12)` alternado con 0.15 s de silencio, sincronizado con `LED_ROJO`.

4. **Evidencia de validación**:
   - *Procedimiento*: Probar claves correctas e incorrectas monitorizando el buzzer y los LEDs.
   - *Resultado*: Tres beeps agudos (1500 Hz) con luz verde para acceso autorizado; tres beeps graves (200 Hz) con luz roja para acceso denegado.

---

### RNF-01: Prevención de rebote físico del botón (antirrebote / debounce)

1. **Necesidad (Requerimiento)**:
   - El sistema evitará registrar una pulsación física debido al rebote del botón.

2. **Origen / Justificación (Sin Issue específico / abordado en Issue #2 e Issue #3)**:
   - Los pulsadores mecánicos generan rebotes eléctricos de corta duración que pueden registrar falsos dígitos múltiples ante una sola pulsación física.

3. **Cambio implementado (PR #3 - `src/Main_code.py`)**:
   - Configuración de resistencias internas `pull_up_down=GPIO.PUD_UP`.
   - Espera activa a la liberación y retardo de estabilización en `revisar_boton()`:
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
   - *Procedimiento*: Presionar de forma rápida y repetida los pulsadores en GPIO 14, 15 y 18.
   - *Resultado*: Cada pulsación mecánica registra exactamente un incremento en el arreglo `secuencia`, sin duplicaciones por rebote.

---

### RNF-02: Conservación segura de clave administrable

1. **Necesidad (Requerimiento)**:
   - La contraseña válida deberá conservarse de forma segura durante la ejecución del sistema y solo podrá modificarse por el administrador.

2. **Origen / Justificación (Issue #1)**:
   - Issue #1 definió el almacenamiento seguro de la clave y su restricción a personal administrativo.

3. **Cambio implementado (PR #11 - `src/Main_code.py`)**:
   - Se eliminó la clave en texto plano como constante de validación directa y se implementó almacenamiento con hash seguro SHA-256 en el archivo persistente `password.txt`.
   - Se añadió un modo de administración mediante argumento por consola (`python src/Main_code.py --admin`) protegido por contraseña de administrador (`ADMIN_PASSWORD = "admin123"`).
   - Se corrigió el formato de entrada de la nueva secuencia para recibir dígitos continuos sin espacios (ej. `123123`), procesados mediante `[int(digito) for digito in entrada]`, asegurando compatibilidad total con la lista de enteros capturada por los pulsadores físicos.
   - Funciones incorporadas: `calcular_hash(secuencia)`, `guardar_password(secuencia)`, `leer_password_guardada()`, `verificar_password(secuencia)` y `cambiar_password()`.

4. **Evidencia de validación**:
   - *Procedimiento*: Ejecución del modo administrativo (`python src/Main_code.py --admin`), autenticación con la clave de administrador, ingreso de nueva secuencia en dígitos continuos sin espacios (ej. `123123`) y posterior validación mediante la pulsación de los botones físicos en el prototipo.
   - *Resultado*: La contraseña se calcula y almacena en hash SHA-256 en `password.txt`. Al reiniciar el sistema e introducir los dígitos correspondientes con los pulsadores físicos, el sistema valida exitosamente la coincidencia de hash (`verificar_password(secuencia)` retorna `True`), otorgando acceso con luz verde y 3 tonos de buzzer.
   - *Estado*: Cumple (PR #11 fusionado a `main`).

---

### RNF-03: Tiempo de respuesta ≤ 1 segundo tras la última pulsación

1. **Necesidad (Requerimiento)**:
   - El sistema deberá evaluar y presentar la respuesta (aprobado/desaprobado) en un tiempo no mayor a 1 segundo tras capturar el último dígito de la secuencia.

2. **Origen / Justificación (Issue #1)**:
   - Issue #1 estipuló que la respuesta del control de acceso debe ser prácticamente instantánea (menor a 1 segundo).

3. **Cambio implementado (PR #7 / prueba de tiempo - `src/Main_code.py`)**:
   - Evaluación síncrona en memoria local: en cuanto se cumple `len(secuencia) == 6`, la sentencia de validación y el llamado a feedback se ejecutan de manera inmediata sin llamadas de red ni bloqueos externos.

4. **Evidencia de validación**:
   - *Procedimiento cuantitativo propuesto*: Medición con `time.perf_counter()` entre la captura de la 6ta pulsación y el inicio de la señalización de salida (`feedback_correcto` / `feedback_incorrecto`).
   - *Resultado estimado*: El procesamiento local toma menos de 0.05 segundos (< 50 ms), holgadamente por debajo del límite de 1 segundo.
   - *Estado*: Pendiente de registrar formalmente las corridas cronometradas en la documentación de evidencia.
