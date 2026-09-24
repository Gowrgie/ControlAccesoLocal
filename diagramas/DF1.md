```mermaid
flowchart LR
    U[Usuario]
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
    C1{¿Datos válidos y consulta correcta?}
    S1[/Resultado de validación/]
    S2[/LED verde o rojo/]
    S3[/Tres tonos cortos del buzzer/]
    S4[/Mensaje de audio "Acceso correcto"/]
    S5[/Confirmación de actualización/]
    U --> E1
    U --> E2
    E1 --> P1
    E2 --> P1
    P1 --> D1
    D1 --> P2
    P2 --> P3
    P3 --> D2
    D2 --> P4
    P4 --> C1
    C1 -->|Sí| P5
    C1 -->|No| P5
    P5 --> S1
    P5 --> S2
    P5 --> S3
    S1 --> U
    S2 --> U
    S3 --> U
    P5 -->|Acceso autorizado| S4
    S4 --> U
    P5 --> P6
    P6 --> D3
    A -->|Usuarios, claves, roles y permisos| P7
    P7 --> D2
    P7 --> S5
    S5 --> A
    ```
