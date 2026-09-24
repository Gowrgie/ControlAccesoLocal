```mermaid
    flowchart TD
    subgraph L1["Usuario"]
        U1(["Persona se aproxima"])
        U2["Se identifica (GUI o botones)"]
    end

    subgraph L2["Sensor / Hardware"]
        H1["Sensor PIR detecta presencia"]
        H2{"GUI y monitor disponibles?"}
        H3["Habilita pantalla de identificacion"]
        H4["Habilita interfaz de botones"]
        H5["LED + buzzer indican resultado"]
        H6["Bocina reproduce Acceso correcto"]
        H7["Motores abren el acceso y regresan a reposo 3s"]
        H8(["Sistema en espera"])
    end

    subgraph L3["Sistema Software"]
        S1["Recibe identificador y clave"]
        S2{"Consulta a BD exitosa?"}
        S3{"Evaluar acceso usuario clave rol permisos"}
        S4["Registrar intento fecha hora usuario mecanismo resultado"]
        S5["Registrar falla de consulta"]
    end

    subgraph L4["Base de Datos MySQL"]
        D1[("Usuarios roles admin servicio tecnico usuario general permisos claves")]
        D2[("Bitacora de intentos")]
    end

    U1 --> H1
    H1 --> H2
    H2 -- Si --> H3
    H2 -- No --> H4
    H3 --> U2
    H4 --> U2
    U2 --> S1
    S1 --> S2
    S2 <-- consulta --> D1
    S2 -- No falla --> S5
    S5 --> S4
    S2 -- Si --> S3
    S3 -- Autorizado --> S4
    S3 -- Sin permiso --> S4
    S3 -- No reconocido --> S4
    S4 --> D2
    S4 --> H5
    H5 -- Solo si autorizado --> H6
    H6 --> H7
    H5 --> H8
    H7 --> H8

    ```