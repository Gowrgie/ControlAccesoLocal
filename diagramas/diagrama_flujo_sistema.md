```mermaid
flowchart TD
    A([Inicio])
    A --> B[Inicializar Raspberry Pi, GPIO, PIR, LEDs, buzzer, audio y motores]
    B --> C[Inicializar conexión con base de datos MySQL]
    C --> D[/Emitir sonido de sistema listo/]
    D --> E[/Esperar detección de presencia mediante sensor PIR/]
    E --> F{¿Persona detectada?}
    F -- No --> E
    F -- Sí --> G{¿Sistema disponible para una nueva operación?}
    G -- No --> E
    G -- Sí --> H[/Mostrar pantalla de identificación/]
    H --> I{¿Método de captura utilizado?}
    I -- Interfaz gráfica --> J[/Capturar identificador y clave desde GUI/]
    I -- Botones físicos --> K[/Capturar identificador y clave mediante botones/]
    J --> L[Consolidar datos capturados]
    K --> M[GPIO detecta pulsaciones]
    M --> N[Aplicar control de rebote]
    N --> O[Registrar identificador y clave]
    O --> P{¿Captura completa?}
    P -- No --> Q{¿Pasaron más de 4 segundos sin pulsación?}
    Q -- No --> K
    Q -- Sí --> R[Limpiar búfer de entrada]
    R --> S[Descartar datos capturados]
    S --> Z[Regresar al estado de espera]
    P -- Sí --> L
    L --> BD[(Base de datos MySQL)]
    BD --> T[Consultar usuario, clave, rol y permisos]
    T --> U{¿Consulta realizada correctamente?}
    U -- No --> V[/Indicar falla del sistema/]
    V --> V1[/Emitir tono largo del buzzer/]
    V1 --> V2[Registrar resultado de falla]
    V2 --> Z
    U -- Sí --> W{¿Usuario reconocido y clave correcta?}
    W -- No --> X[/Encender LED rojo/]
    X --> X1[/Emitir 3 tonos cortos/]
    X1 --> X2[/Mostrar acceso rechazado/]
    X2 --> X3[Registrar intento rechazado]
    X3 --> BD2[(Registro de intentos)]
    BD2 --> Z
    W -- Sí --> Y[Identificar rol del usuario]
    Y --> Y1{¿Rol y permisos autorizan el acceso?}
    Y1 -- No --> AA[/Encender LED rojo/]
    AA --> AA1[/Emitir 3 tonos cortos/]
    AA1 --> AA2[/Mostrar usuario sin permiso/]
    AA2 --> AA3[Registrar intento sin permiso]
    AA3 --> BD3[(Registro de intentos)]
    BD3 --> Z
    Y1 -- Sí --> AB[/Encender LED verde/]
    AB --> AB1[/Emitir 3 tonos cortos/]
    AB1 --> AB2[/Mostrar acceso autorizado/]
    AB2 --> AB3[/Reproducir mensaje "Acceso correcto"/]
    AB3 --> AC[Activar los dos motores de apertura]
    AC --> AD[Esperar 3 segundos]
    AD --> AE[Regresar ambos motores a posición de reposo]
    AE --> AF[Registrar intento autorizado]
    AF --> BD4[(Registro de intentos)]
    BD4 --> Z
    Z --> AG[/Apagar LEDs y finalizar señales activas/]
    AG --> AH[Limpiar datos de la operación]
    AH --> D
    ```