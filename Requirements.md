# Requisitos del sistema
## Requerimientos Funcionales
RF-01. El sistema deberá capturar la secuencia introducida, compararla con una clave válida y determinar si el acceso se autoriza o se rechaza.

RF-02. El sistema capturara una clave de 4 a 6 pulsaciones.

RF-03. El sistema mostrara en la pantalla si la clave es válida o no es válida.

RF-04. El sistema se reiniciara después de cada captura para permitir nuevos datos.

RF-05. El sistema permitira modificar la contraseña valida en el programa.

RF-06. Si transcurren más de 5 segundos sin recibir una nueva pulsación durante una captura incompleta, el sistema limpiará el búfer de entrada, descartará los datos introducidos y regresará automáticamente a la pantalla de inicio.

RF-07. Tras acumular 3 intentos consecutivos incorrectos, el sistema se bloqueará durante 30 a 60 segundos, impidiendo el registro de nuevas pulsaciones y mostrando un mensaje de advertencia / cuenta regresiva en pantalla.

## Requerimientos No Funcionales
RNF-01. El sistema evitara registrar una pulsacion fisica debido al rebote del botón

RNF-02. Tras capturar el último dígito de la secuencia, el sistema deberá evaluar la clave y presentar la respuesta

RNF-03. El sistema guardara en una variable global la clave hasta que se genere una nueva
