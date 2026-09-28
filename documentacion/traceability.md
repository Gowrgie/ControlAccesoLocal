# Trazabilidad

Este archivo relaciona los requerimientos del sistema con los cambios realizados en el repositorio y la evidencia disponible para su validación.

## Requerimientos funcionales

| Requerimiento | Issue | PR / cambio | Evidencia de validación |
|---|---|---|---|
| RF-01 | #5 | PR #9, #11 | En desarrollo. El código actual captura y valida una secuencia, pero aún falta integrar completamente la validación con la base de datos. |
| RF-02 | #35, #39 | PR #36, #38 | En desarrollo. La base de datos ya contempla un identificador y una clave por usuario; falta completar su integración con el sistema. |
| RF-03 | #5 | PR #7 | Se verificó en el código el uso del LED verde para acceso correcto y del LED rojo para acceso incorrecto. |
| RF-04 | #5 | PR #9 | Se verificó que después de validar una secuencia se limpian los datos y el sistema queda listo para una nueva captura. |
| RF-05 | #5 | PR #9 | Se verificó que una captura incompleta se cancela después de más de 4 segundos sin pulsaciones. |
| RF-06 | #5 | PR #9 | Se verificó que el buzzer emite un sonido cuando el sistema queda listo para una nueva captura. |
| RF-07 | #5 | PR #7 | En desarrollo. Los tres tonos para acceso correcto o incorrecto están implementados; falta completar el tono largo para fallas del sistema. |
| RF-08 | #23, #24 | PR #37 | Pendiente de implementación. La detección mediante sensor PIR ya está contemplada en los diagramas del sistema. |
| RF-09 | #29 | PR #40 | Pendiente de implementación. Se diseñaron los wireframes de la interfaz gráfica, pero falta integrarla al sistema. |
| RF-10 | #29 | PR #40 | Pendiente de implementación. La interfaz para el monitor ya fue diseñada, pero todavía no está conectada a la Raspberry Pi. |
| RF-11 | #33, #35, #39 | PR #32, #36, #38 | En desarrollo. Se creó la base de datos para usuarios, roles e intentos de acceso y se trabaja en su conexión con el código. |
| RF-12 | #28, #35 | PR #30, #36 | En desarrollo. La base de datos ya maneja usuarios y roles, pero falta terminar la integración de los tres roles definidos. |
| RF-13 | #35, #39 | PR #36, #38 | En desarrollo. La estructura de la base de datos contempla distintos resultados de acceso, pero falta completar la validación desde el programa. |
| RF-14 | #5, #39 | PR #3, #38 | En desarrollo. Los botones físicos ya permiten capturar la clave; falta compartir completamente la misma validación usada por la futura interfaz gráfica. |
| RF-15 | #23, #24 | PR #37 | Pendiente de implementación. El funcionamiento mediante botones cuando la interfaz no esté disponible ya está definido en los diagramas. |
| RF-16 | #23, #24 | PR #37 | Pendiente de implementación. El mensaje de audio "Acceso correcto" está contemplado en el flujo, pero aún no se reproduce desde el código. |
| RF-17 | #23, #24 | PR #37 | Pendiente de implementación. La apertura mediante dos motores y su regreso a reposo después de 3 segundos ya está documentada. |
| RF-18 | #5, #24 | PR #9, #37 | En desarrollo. El modo actual con botones regresa a espera después de cada captura; falta extender este comportamiento a todo el sistema. |

## Requerimientos no funcionales

| Requerimiento | Issue | PR / cambio | Evidencia de validación |
|---|---|---|---|
| RNF-01 | #5 | PR #3, #9 | Se implementó control de rebote en la lectura de los botones para evitar registrar una misma pulsación varias veces. |
| RNF-02 | #35, #39 | PR #36, #38 | En desarrollo. La base de datos almacena usuario, clave, rol y permisos; falta restringir completamente las modificaciones al administrador. |
| RNF-03 | #5 | PR #9 | En desarrollo. La respuesta del sistema es inmediata en las pruebas actuales, pero falta realizar una medición formal del límite de 1 segundo. |
| RNF-04 | #24 | PR #37 | Pendiente de implementación. El uso del sensor PIR está definido, pero aún falta comprobar su tiempo de respuesta. |
| RNF-05 | #29 | PR #40 | Pendiente de implementación. Se diseñaron wireframes sencillos para la interfaz, pero falta validar su uso en el sistema funcionando. |
| RNF-06 | #39 | PR #38 | Pendiente de implementación. Falta aplicar y comprobar el límite de 2 segundos en las consultas a MySQL. |
| RNF-07 | #5, #24 | PR #3, #37 | En desarrollo. La captura mediante botones ya funciona de manera independiente; falta probar el cambio automático cuando la GUI no esté disponible. |
| RNF-08 | #24 | PR #37 | Pendiente de implementación. El mensaje de audio está definido, pero aún falta comprobar que sea audible a un metro de distancia. |
| RNF-09 | #35, #39 | PR #36, #38 | En desarrollo. Existe la tabla de intentos de acceso; falta comprobar la protección y conservación de los registros. |
| RNF-10 | #24 | PR #37 | Pendiente de implementación. El flujo contempla una operación de acceso a la vez, pero aún falta aplicar el control en el código. |