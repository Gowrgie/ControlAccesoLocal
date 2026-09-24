```mermaid
flowchart LR
    U[Usuario]
    A[Administrador]
    S["Sistema de Control de Acceso Local"]
    U -->|Identificación y clave mediante GUI o botones| S
    S -->|Resultado de validación de acceso| U
    S -->|Indicadores LED, buzzer y mensajes de audio| U
    S -->|Activación del mecanismo de acceso autorizado| U
    A -->|Gestión de usuarios, claves, roles y permisos| S
    S -->|Confirmación de cambios realizados| A
    ```