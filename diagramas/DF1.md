```mermaid
flowchart LR
    U[Usuario]
    A[/Pulsaciones de botones/]
    B[Capturar secuencia]
    C[(Secuencia capturada)]
    D[Validar secuencia]
    E[(Contraseña válida)]
    F[Comparar contraseña]
    G[/Resultado de validación/]
    H[/LED verde o rojo/]
    I[/Sonido de sistema listo/]
    U --> A
    A --> B
    B --> C
    C --> D
    D --> F
    E --> F
    F --> G
    G --> H
    H --> U
    F --> I
    I --> U
    ```
