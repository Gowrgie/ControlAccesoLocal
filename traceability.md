# 8. Trazabilidad

El archivo `traceability.md` deberá permitir reconstruir **por qué existe un cambio y cómo fue verificado**.

| Requerimiento | Issue | PR / cambio | Evidencia de validación |
| :--- | :--- | :--- | :--- |
| RF-01 | Issue #5 | PR #7 / PR #9 | Demostración: una secuencia válida autoriza el acceso. Al ingresar la clave correcta `[1, 2, 3, 1, 2, 3]` mediante los pulsadores físicos, el sistema valida la coincidencia contra `PASSWORD_VALIDA`, enciende el LED verde (GPIO 23) y genera tres tonos audibles de confirmación (1500 Hz) con el buzzer PWM (GPIO 25), autorizando el acceso. Al ingresar una secuencia incorrecta, activa el LED rojo (GPIO 24) y reproduce tres tonos graves (200 Hz), denegando el acceso. |

---

### Relación lógica y reconstrucción del cambio (RF-01)

No se busca llenar una tabla únicamente por cumplir. Debe existir una relación lógica entre la necesidad, el cambio realizado y la manera en que fue validado:

1. **Necesidad (Requerimiento)**:
   - **RF-01**: El sistema deberá capturar la secuencia introducida, compararla con una clave válida y determinar si el acceso se autoriza o se rechaza.

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
