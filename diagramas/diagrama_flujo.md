```mermaid
flowchart TD
    A([Inicio]) --> B[Inicializar sistema]
    B --> C[/Emitir sonido de sistema listo/]
    C --> D[/Esperar detección de presencia por sensor PIR/]
    D --> E{¿Persona detectada?}
    E -- No --> D
    E -- Sí --> F[/Mostrar pantalla de identificación/]
    F --> G{¿Método de captura disponible?}
    G -- Interfaz gráfica --> H[/Capturar usuario y clave desde GUI/]
    G -- Botones físicos --> I[/Capturar usuario y clave desde botones/]
    I --> J{¿Captura completa?}
    J -- No --> K{¿Han pasado más de 4 segundos sin pulsación?}
    K -- No --> I
    K -- Sí --> L[Limpiar búfer de entrada]
    L --> M[Descartar datos introducidos]
    M --> Z[Regresar al estado de espera]
    J -- Sí --> N[Consolidar datos capturados]
    H --> N
    N --> O[Consultar usuario, clave, rol y permisos en MySQL]
    O --> P{¿Consulta realizada correctamente?}
    P -- No --> Q[/Indicar falla del sistema/]
    Q --> Q1[/Emitir tono largo del buzzer/]
    Q1 --> R[Registrar intento y falla en la base de datos]
    R --> Z
    P -- Sí --> S{¿Usuario reconocido e información correcta?}
    S -- No --> T[/Encender LED rojo/]
    T --> T1[/Emitir 3 tonos cortos/]
    T1 --> T2[/Mostrar acceso rechazado/]
    T2 --> U[Registrar intento rechazado]
    U --> Z
    S -- Sí --> V{¿Rol y permisos autorizan el acceso?}
    V -- No --> W[/Encender LED rojo/]
    W --> W1[/Emitir 3 tonos cortos/]
    W1 --> W2[/Mostrar usuario sin permiso/]
    W2 --> X[Registrar intento sin permiso]
    X --> Z
    V -- Sí --> Y[/Encender LED verde/]
    Y --> Y1[/Emitir 3 tonos cortos/]
    Y1 --> Y2[/Mostrar acceso autorizado/]
    Y2 --> Y3[/Reproducir mensaje "Acceso correcto"/]
    Y3 --> Y4[Activar los dos motores de apertura]
    Y4 --> Y5[Esperar 3 segundos]
    Y5 --> Y6[Regresar ambos motores a posición de reposo]
    Y6 --> Y7[Registrar intento autorizado]
    Y7 --> Z[Regresar al estado de espera]
    Z --> C
    ```