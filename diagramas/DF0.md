```mermaid
flowchart LR
    U[Usuario]
    A[Administrador]
    ST[Servicio técnico]
    S["Sistema de Control de Acceso Local"]
    U -->|Identificación y clave mediante GUI o botones| S
    S -->|Resultado de validación de acceso| U
    S -->|Indicadores LED, buzzer y mensajes de audio| U
    S -->|Activación de los dos motores al autorizar acceso| U
    A -->|Gestión de usuarios, claves, roles y permisos| S
    S -->|Confirmación de cambios realizados| A
    ST -->|Acceso según permisos asignados| S
    S -->|Resultado de validación de acceso| ST
    ```