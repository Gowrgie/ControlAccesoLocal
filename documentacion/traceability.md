# Trazabilidad

Este archivo relaciona los requerimientos del sistema con los cambios realizados en el repositorio y la evidencia disponible para su validación.

## Requerimientos funcionales

| Requerimiento | Issue | PR / cambio | Evidencia de validación |
|---|---|---|---|
| RF-01 | #5 | PR #9, #11 | El sistema captura los datos ingresados, los compara con la información almacenada y determina si el acceso se autoriza o se rechaza. |
| RF-02 | #35, #39 | PR #36, #38 | El sistema identifica al usuario y recibe una clave de entre 4 y 6 pulsaciones para realizar la validación. |
| RF-03 | #5 | PR #7 | El sistema enciende el LED verde cuando el acceso es válido y el LED rojo cuando es rechazado. |
| RF-04 | #5 | PR #9 | Después de cada operación se limpian los datos capturados y el sistema queda listo para una nueva entrada. |
| RF-05 | #5 | PR #9 | Si pasan más de 4 segundos sin una nueva pulsación, la captura incompleta se descarta y el sistema regresa al estado de espera. |
| RF-06 | #5 | PR #9 | El buzzer emite un sonido cuando el sistema regresa al estado de espera y está listo para una nueva captura. |
| RF-07 | #5 | PR #7 | El buzzer emite tres tonos cortos al validar un acceso y un tono largo cuando ocurre una falla del sistema. |
| RF-08 | #23, #24 | PR #37 | El sensor PIR detecta la presencia de una persona y habilita la interacción con el sistema. |
| RF-09 | #29 | PR #40 | La interfaz gráfica permite ingresar el usuario y la clave, además de mostrar el resultado de la validación. |
| RF-10 | #29 | PR #40 | La interfaz gráfica se muestra en el monitor conectado a la Raspberry Pi para permitir la interacción con el usuario. |
| RF-11 | #33, #35, #39 | PR #32, #36, #38 | MySQL almacena la información de usuarios y registra cada intento de acceso con sus datos correspondientes. |
| RF-12 | #28, #35 | PR #30, #36 | El sistema identifica los roles de administrador, servicio técnico y usuario general, aplicando permisos diferentes a cada uno. |
| RF-13 | #35, #39 | PR #36, #38 | El sistema valida usuario, clave, rol y permisos, diferenciando accesos autorizados, sin permiso, datos incorrectos y fallas de consulta. |
| RF-14 | #5, #39 | PR #3, #38 | Los botones físicos permiten ingresar la clave utilizando la misma lógica de validación empleada por la interfaz gráfica. |
| RF-15 | #23, #24 | PR #37 | Si la interfaz gráfica o el monitor no están disponibles, el acceso puede completarse mediante los botones físicos. |
| RF-16 | #23, #24 | PR #37 | Cuando el acceso es autorizado, el sistema reproduce el mensaje de audio "Acceso correcto". |
| RF-17 | #23, #24 | PR #37 | Al autorizar el acceso se activa un motor y, después de 3 segundos, ambos regresan a su posición de reposo. |
| RF-18 | #5, #24 | PR #9, #37 | Después de cada operación el sistema regresa al estado de espera, sin importar el resultado o método de captura utilizado. |

## Requerimientos no funcionales

| Requerimiento | Issue | PR / cambio | Evidencia de validación |
|---|---|---|---|
| RNF-01 | #5 | PR #3, #9 | Se aplica control de rebote en los botones para evitar que una misma pulsación sea registrada más de una vez. |
| RNF-02 | #35, #39 | PR #36, #38 | La información de usuarios, claves, roles y permisos se conserva en la base de datos y su modificación está restringida al administrador. |
| RNF-03 | #5 | PR #9 | El sistema presenta el resultado de la validación dentro del tiempo máximo establecido de 1 segundo. |
| RNF-04 | #24 | PR #37 | El sensor PIR detecta la presencia y habilita la interacción dentro del tiempo máximo de 1 segundo. |
| RNF-05 | #29 | PR #40 | La interfaz gráfica permite realizar la identificación y validación de forma sencilla y sin capacitación previa. |
| RNF-06 | #39 | PR #38 | Las consultas a MySQL se realizan dentro del límite de 2 segundos y un tiempo mayor se maneja como falla. |
| RNF-07 | #5, #24 | PR #3, #37 | El sistema permite continuar la operación mediante botones físicos cuando la interfaz gráfica o el monitor no están disponibles. |
| RNF-08 | #24 | PR #37 | El mensaje de audio "Acceso correcto" puede escucharse a una distancia mínima de 1 metro del punto de acceso. |
| RNF-09 | #35, #39 | PR #36, #38 | Los intentos de acceso quedan almacenados para su consulta posterior y no pueden modificarse desde las interfaces de acceso. |
| RNF-10 | #24 | PR #37 | El sistema procesa una sola operación de acceso a la vez para evitar validaciones simultáneas por GUI y botones. |