```mermaid
flowchart LR
    U[Usuario general]
    ST[Servicio técnico]
    A[Administrador]
    E1[/Identificación y clave por interfaz gráfica/]
    E2[/Identificación y clave por botones físicos/]
    P1[Capturar datos de acceso]
    P2[Validar datos ingresados]
    P3[Consultar información de acceso]
    P4[Evaluar usuario, clave, rol y permisos]
    P5[Generar resultado de acceso]
    P6[Registrar intento de acceso]
    P7[Actualizar información de acceso]
    D1[(Datos capturados)]
    D2[(Base de datos MySQL)]
    D3[(Registro de intentos de acceso)]
    C1{¿Consulta correcta?}
    C2{¿Acceso autorizado según rol y permisos?}
    S1[/Resultado de validación/]
    S2[/LED verde o rojo/]
    S3[/Tres tonos cortos del buzzer/]
    S4[/Mensaje de audio "Acceso correcto"/]
    S5[/Orden de apertura a dos motores/]
    S6[/Confirmación de actualización/]
    S7[/Tono largo por falla del sistema/]
    U --> E1
    U --> E2
    ST --> E1
    ST --> E2
    A --> E1
    A --> E2
    E1 --> P1
    E2 --> P1
    P1 --> D1
    D1 --> P2
    P2 --> P3
    P3 --> D2
    D2 -->|Usuario, clave, rol y permisos| P4
    P4 --> C1
    C1 -- No --> S7
    S7 --> S1
    C1 -- Sí --> C2
    C2 -- No --> P5
    C2 -- Sí --> P5
    P5 --> S1
    P5 --> S2
    P5 --> S3
    S1 --> U
    S1 --> ST
    S1 --> A
    S2 --> U
    S2 --> ST
    S2 --> A
    S3 --> U
    S3 --> ST
    S3 --> A
    C2 -- Sí --> S4
    S4 --> S5
    S4 --> U
    S4 --> ST
    S4 --> A
    P5 --> P6
    P6 --> D3
    A -->|Gestionar usuarios, claves, roles y permisos| P7
    P7 --> D2
    P7 --> S6
    S6 --> A
    ```
