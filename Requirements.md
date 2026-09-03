# Requisitos del sistema
## Requerimientos Funcionales
RF-01. El sistema deberá capturar la secuencia introducida, compararla con una clave válida y determinar si el acceso se autoriza o se rechaza.

RF-02. El sistema capturara una clave de 4 a 6 pulsaciones.

RF-03. El sistema mostrara por medio de luces led si la clave es válida(verde) o no es válida(rojo).

RF-04. El sistema se reiniciara después de cada captura para permitir nuevos datos.

RF-05. Si transcurren más de 4 segundos sin recibir una nueva pulsación durante una captura incompleta, el sistema limpiará el búfer de entrada, descartará los datos introducidos y regresará automáticamente a la pantalla de inicio.

RF-06. El sistema emitira un sonido por cada vez que se reinicie el sistema y se pueda volver a ingresar la contraseña.

## Requerimientos No Funcionales
RNF-01. El sistema evitara registrar una pulsacion fisica debido al rebote del botón

RNF-02. La contraseña válida deberá conservarse de forma segura durante la ejecución del sistema y solo podrá modificarse por el administrador.

RNF-03. El sistema deberá evaluar y presentar la respuesta (aprobado/desaprobado) en un tiempo no mayor a 1 segundo tras capturar el último dígito de la secuencia.
