```mermaid
flowchart TD
    A([Inicio])
    A --> B[Inicializar Raspberry Pi y configurar GPIO]
    B --> C[/Esperar pulsación de botón/]
    C --> D[/Botón físico presionado/]
    D --> E[GPIO detecta cambio de estado]
    E --> F[Raspberry Pi registra la pulsación]
    F --> G[Aplicar control de rebote]
    G --> H[Agregar valor a la secuencia]
    H --> I{¿Secuencia completa?}
    I -- No --> T{¿Pasaron más de 4 segundos sin pulsación?}
    T -- No --> C
    T -- Sí --> U[Descartar secuencia y reiniciar]
    U --> C
    I -- Sí --> J[Comparar secuencia con contraseña válida]
    J --> K{¿Contraseña correcta?}
    K -- Sí --> L[/Encender LED verde/]
    L --> M[/Activar buzzer/]
    K -- No --> N[/Encender LED rojo/]
    N --> O[/Activar buzzer/]
    M --> P[Esperar tiempo de respuesta]
    O --> P
    P --> Q[/Apagar LED y buzzer/]
    Q --> R[Limpiar secuencia]
    R --> S[Reiniciar captura]
    S --> C
    ```