```mermaid
flowchart LR
    U[Usuario]
    A[Administrador]
    E1[/Pulsaciones de botones/]
    P1[Capturar secuencia]
    P2[Validar secuencia]
    P3[Comparar contraseña]
    P4[Generar resultado]
    P5[Actualizar contraseña]
    D1[(Secuencia capturada)]
    D2[(Contraseña válida)]
    S1[/Resultado de validación/]
    S2[/LED verde o rojo/]
    S3[/Sonido de sistema listo/]
    S4[/Confirmación de cambio/]
    U --> E1
    E1 --> P1
    P1 --> D1
    D1 --> P2
    P2 --> P3
    D2 --> P3
    P3 --> P4
    P4 --> S1
    S1 --> S2
    S2 --> U
    P4 --> S3
    S3 --> U
    A -->|Nueva contraseña| P5
    P5 --> D2
    P5 --> S4
    S4 --> A
    ```
