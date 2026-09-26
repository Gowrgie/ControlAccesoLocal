```mermaid
flowchart TD
    A([Inicio]) --> B[Inicializar sistema]
    B --> C[/Emitir sonido de sistema listo/]
    C --> D[Estado de espera]
    D --> E[/Esperar detección de presencia por sensor PIR/]
    E --> F{¿Persona detectada?}
    F -- No --> E
    F -- Sí --> G[Presencia detectada]
    G --> H{¿Método de captura disponible?}
    H -- Interfaz gráfica --> I[/Capturar usuario y clave desde GUI/]
    H -- Botones físicos --> J[/Capturar usuario y clave mediante botones/]
    H -- GUI no disponible --> J
    J --> K{¿Captura completa?}
    K -- No --> L{¿Han pasado más de 4 segundos sin pulsación?}
    L -- No --> J
    L -- Sí --> M[Limpiar búfer de entrada]
    M --> N[Descartar datos capturados]
    N --> D
    K -- Sí --> O[Datos capturados]
    I --> O
    O --> P[(Base de datos MySQL)]
    P --> Q[Consultar usuario, clave, rol y permisos]
    Q --> R{¿Consulta correcta?}
    R -- No --> S[Estado de falla]
    S --> S1[/Emitir tono largo del buzzer/]
    S1 --> T[Registrar intento de acceso]
    T --> U[(Registro de intentos)]
    U --> D
    R -- Sí --> V{¿Usuario reconocido y clave correcta?}
    V -- No --> W[Estado rechazado]
    W --> W1[/Encender LED rojo/]
    W1 --> W2[/Emitir 3 tonos cortos/]
    W2 --> W3[/Mostrar acceso rechazado/]
    W3 --> T
    V -- Sí --> X[Identificar rol del usuario]
    X --> Y{¿Rol y permisos autorizan el acceso?}
    Y -- No --> Z[Estado sin permiso]
    Z --> Z1[/Encender LED rojo/]
    Z1 --> Z2[/Emitir 3 tonos cortos/]
    Z2 --> Z3[/Mostrar usuario sin permiso/]
    Z3 --> T
    Y -- Sí --> AA[Estado autorizado]
    AA --> AA1[/Encender LED verde/]
    AA1 --> AA2[/Emitir 3 tonos cortos/]
    AA2 --> AA3[/Mostrar acceso autorizado/]
    AA3 --> AA4[/Reproducir mensaje "Acceso correcto"/]
    AA4 --> AB[Activar los dos motores]
    AB --> AC[Estado de apertura]
    AC --> AD[Esperar 3 segundos]
    AD --> AE[Regresar ambos motores a posición de reposo]
    AE --> T
    T --> U
    U --> AF[Limpiar datos de la operación]
    AF --> D
    ```