```mermaid
flowchart TD
    subgraph L1["User"]
        U1(["Person approaches access point"])
        U2["Identifies through GUI or physical buttons"]
        U3["Uses facial recognition"]
        U4["Administrator starts new user enrollment"]
    end
    subgraph L2["Sensor / Hardware"]
        H1["PIR sensor detects presence"]
        H2{"GUI and monitor available?"}
        H3["Enable identification screen"]
        H4["Enable physical button interface"]
        H5["Camera captures live facial image"]
        H6["LED and buzzer indicate result"]
        H7["Speaker plays Access granted"]
        H8["Motor opens access and returns to rest after 3 seconds"]
        H9(["System returns to standby"])
    end
    subgraph L3["Software System"]
        S1["Receive user ID and passcode"]
        S2["Perform local facial detection and identification"]
        S3{"Database query successful?"}
        S4{"Evaluate user, passcode, role, and permissions"}
        S5{"Registered face identified?"}
        S6["Associate biometric representation with local user record"]
        S7["Register access attempt with date, time, user, mechanism, and result"]
        S8["Register database query failure"]
        S9["Generate biometric representation locally"]
        S10["Confirm successful user enrollment"]
    end
    subgraph L4["MySQL Database"]
        D1[("Users, passcodes, roles, permissions")]
        D2[("Biometric data linked to local users")]
        D3[("Access attempt logs")]
    end
    U1 --> H1
    H1 --> H2
    H2 -- Yes --> H3
    H2 -- No --> H4
    H3 --> U2
    H4 --> U2
    U2 --> S1
    S1 --> S3
    S3 <-- Query --> D1
    S3 -- No --> S8
    S8 --> S7
    S3 -- Yes --> S4
    S4 -- Authorized --> S7
    S4 -- No permission --> S7
    S4 -- Unrecognized / invalid --> S7
    U3 --> H5
    H5 --> S2
    S2 --> S5
    S5 -- No --> S7
    S5 -- Yes --> S6
    S6 --> D2
    S6 --> S4
    U4 --> H5
    H5 --> S9
    S9 --> D2
    S9 --> S10
    S7 --> D3
    S7 --> H6
    H6 -- Authorized only --> H7
    H7 --> H8
    H6 --> H9
    H8 --> H9
    S10 --> H9
    ```