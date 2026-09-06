```mermaid
flowchart LR
    U[Usuario]
    A[Administrador]
    S["Sistema de Control de Acceso Local"]
    U -->|Secuencia de pulsaciones| S
    S -->|Resultado de acceso| U
    S -->|Indicador LED y sonido| U
    A -->|Nueva contraseña| S
    S -->|Confirmación de cambio| A
    ```