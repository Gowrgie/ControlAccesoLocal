´´´mermaid
flowchart TD
    A([Inicio]) --> B[Inicializar sistema]
    B --> C[/Emitir sonido de sistema listo/]
    C --> D[/Esperar pulsación/]
    D --> E[Registrar pulsación]
    E --> G[Agregar pulsación a la secuencia]
    G --> H{¿Secuencia completa?}
    H -- No --> I{¿Han pasado más de 4 segundos sin pulsación?}
    I -- No --> D
    I -- Sí --> J[Limpiar búfer de entrada]
    J --> K[Descartar secuencia]
    K --> L[Reiniciar captura]
    L --> C
    H -- Sí --> M[Comparar secuencia con contraseña válida]
    M --> N{¿Contraseña correcta?}
    N -- Sí --> O[/Encender LED verde/]
    O --> P[Autorizar acceso]
    N -- No --> Q[/Encender LED rojo/]
    Q --> R[Rechazar acceso]
    P --> S[Esperar hasta 1 segundo]
    R --> S
    S --> T[/Apagar LEDs/]
    T --> U[Limpiar secuencia capturada]
    U --> V[Reiniciar captura]
    V --> C
    ´´´