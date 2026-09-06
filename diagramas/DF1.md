```mermaid
flowchart LR
    U[Usuario]
    A[Administrador]
    P1[Capturar secuencia]
    P2[Validar secuencia]
    P3[Comparar contraseña]
    P4[Generar resultado]
    P5[Actualizar contraseña]
    D1[(Contraseña válida)]
    D2[(Secuencia capturada)]
    U -->|Pulsaciones de botones| P1
    P1 -->|Secuencia ingresada| D2
    D2 -->|Secuencia capturada| P2
    P2 -->|Secuencia válida| P3
    D1 -->|Contraseña almacenada| P3
    P3 -->|Resultado de comparación| P4
    P4 -->|Acceso autorizado / rechazado| U
    P4 -->|LED verde / rojo| U
    A -->|Nueva contraseña| P5
    P5 -->|Contraseña actualizada| D1
    P5 -->|Confirmación de cambio| A
    ```
