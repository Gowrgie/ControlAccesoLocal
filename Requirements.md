# Requisitos del sistema
## Requerimientos Funcionales
RF-01. El sistema deberá capturar la secuencia introducida, compararla con la información almacenada en la base de datos y determinar si el acceso se autoriza o se rechaza.

RF-02. El sistema capturará un identificador de usuario y una clave de 4 a 6 pulsaciones.

RF-03. El sistema mostrara por medio de luces led si la clave es válida(verde) o no es válida(rojo).

RF-04. El sistema se reiniciara después de cada captura para permitir nuevos datos.

RF-05. Si transcurren más de 4 segundos sin recibir una nueva pulsación durante una captura incompleta, el sistema limpiará el búfer de entrada, descartará los datos introducidos y regresará automáticamente a la pantalla de inicio(estado de espera).

RF-06. El sistema emitira un sonido cada vez que regrese al estado de espera y quede listo para una nueva captura.

RF-07. El sistema emitirá tres tonos cortos del buzzer al evaluar la secuencia ingresada, tanto si el acceso es autorizado como si es rechazado, coincidiendo con el encendido del LED verde o rojo correspondiente. Ante una falla del sistema emitirá un tono largo.

RF-08. El sistema detectará la presencia de una persona mediante un sensor PIR y, estando en espera, iniciará o habilitará la interacción mostrando la pantalla de identificación. La detección del PIR no autorizará el acceso por sí sola.

RF-09. El sistema contará con una interfaz gráfica sencilla desarrollada en Python que permitirá al usuario identificarse, introducir su clave y ver el resultado de la validación.

RF-10. El sistema mostrará la interfaz gráfica en un monitor conectado a la Raspberry Pi.

RF-11. El sistema almacenará y consultará la información necesaria en una base de datos MySQL, y registrará cada intento de acceso con fecha y hora, usuario, mecanismo utilizado (interfaz gráfica o botones) y resultado.

RF-12. El sistema identificará a cada usuario dentro del sistema y le asignará uno de al menos dos roles o niveles de acceso (por ejemplo, administrador y usuario general) con permisos diferenciables.

RF-13. El sistema validará el acceso utilizando la información almacenada en la base de datos (usuario, clave, rol y permisos) y distinguirá entre usuario autorizado, usuario autorizado pero sin permiso, información incorrecta o usuario no reconocido y falla en la consulta de la base de datos, sin tratar esta última como un rechazo.

RF-14. El sistema conservará la interfaz física de botones de la primera versión para introducir la clave, y utilizará la misma lógica de validación que la interfaz gráfica, sin duplicarla.

RF-15. Cuando la interfaz gráfica o el monitor no se encuentren disponibles, el sistema permitirá completar la autenticación, el resultado y el registro del intento mediante los botones físicos.

RF-16. Cuando el acceso sea autorizado, el sistema reproducirá por bocina o altavoz el mensaje "Acceso correcto".

RF-17. Cuando el acceso sea autorizado, el sistema activará un mecanismo físico sencillo (servo, relé o equivalente de prototipo) que represente la apertura del acceso y lo regresará a su posición de reposo después de 3 segundos. Con cualquier otro resultado no se activará.

RF-18. El sistema regresará a un estado de espera después de completar cada operación, sin importar el resultado ni la interfaz utilizada, quedando listo para detectar una nueva presencia.

## Requerimientos No Funcionales
RNF-01. El sistema evitara registrar una pulsacion fisica debido al rebote del botón

RNF-02. La contraseña válida deberá conservarse de forma segura durante la ejecución del sistema y solo podrá modificarse por el administrador.

RNF-03. El sistema deberá evaluar y presentar la respuesta (aprobado/desaprobado) en un tiempo no mayor a 1 segundo tras capturar el último dígito de la secuencia.
