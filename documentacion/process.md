```mermaid
flowchart TD
    %% USER LAYER
    subgraph L1["Users"]
        U1(["Person approaches access point"])
        U2["Uses GUI or physical buttons"]
        U3["Uses facial recognition"]
        U4["Uses mobile application"]
        U5["Administrator requests facial enrollment"]
    end
    %% HARDWARE LAYER
    subgraph L2["Sensor / Hardware"]
        H1["PIR sensor detects presence"]
        H2{"Person detected?"}
        H3{"GUI and monitor available?"}
        H4["Enable identification screen"]
        H5["Enable physical buttons"]
        H6["Camera captures live facial image"]
        H7["LED and buzzer indicate result"]
        H8["Speaker plays Access granted"]
        H9["Motor opens access and returns to rest after 3 seconds"]
        H10(["System returns to standby"])
    end
    %% MOBILE APPLICATION
    subgraph L3["Mobile Application"]
        M1["Enter user ID and passcode"]
        M2["Send access request through local network"]
        M3["Display access result"]
        M4["Display technical failure or unavailable request"]
        M5["Return mobile app to standby"]
    end
    %% LOCAL API
    subgraph L4["Local API Service"]
        API1["Receive mobile request on Raspberry Pi"]
        API2{"Encrypted and authenticated connection?"}
        API3{"PIR presence detected?"}
        API4["Forward credentials to shared validation"]
        API5["Reject insecure request"]
        API6["Reject request without detected presence"]
        API7["Return one of four access results"]
    end
    %% SOFTWARE LAYER
    subgraph L5["Software System"]
        S0{"System available for a new operation?"}
        S1["Reserve access operation"]
        S2{"Access mechanism or operation?"}
        S3["Capture and prepare user credentials"]
        S4["Apply debounce to physical button inputs"]
        S5{"Capture complete?"}
        S6{"More than 4 seconds without input?"}
        S7["Discard incomplete capture"]
        S8["Query user, stored passcode hash, role, and permissions"]
        S9{"Database query successful?"}
        S10{"Registered user and correct passcode?"}
        S11["Perform local facial detection and identification"]
        S12{"Registered face identified?"}
        S13["Retrieve linked user and permissions"]
        S14{"User information retrieved successfully?"}
        S15{"Role and permissions allow access?"}
        R1["Authorized"]
        R2["Without permission"]
        R3["Unrecognized"]
        R4["System error"]
        S16["Register access attempt with user, method, result, date, and time"]
        S17["Record technical failure if database is available"]
        S18["Send result to requesting interface"]
        S19["Release operation and clear temporary data"]
        EN1{"Administrator authorized?"}
        EN2["Capture guided facial samples"]
        EN3["Validate capture quality and facial poses"]
        EN4{"Capture requirements satisfied?"}
        EN5["Generate biometric representations locally"]
        EN6["Associate biometric data with local user"]
        EN7{"Enrollment saved successfully?"}
        EN8["Confirm successful facial enrollment"]
        EN9["Display enrollment error"]
    end
    %% DATABASE LAYER
    subgraph L6["Local MySQL Database"]
        D1[("Users, hashed passcodes, roles, and permissions")]
        D2[("Biometric data linked to local users")]
        D3[("Access attempt logs")]
    end
    %% PRESENCE DETECTION
    U1 --> H1
    H1 --> H2
    H2 -- No --> H10
    H2 -- Yes --> S0
    %% MOBILE REQUEST
    U4 --> M1
    M1 --> M2
    M2 --> API1
    API1 --> API2
    API2 -- No --> API5
    API5 --> M4
    M4 --> M5
    API2 -- Yes --> API3
    API3 -- No --> API6
    API6 --> M4
    API3 -- Yes --> S0
    %% SHARED OPERATION CONTROL
    U5 --> S0
    S0 -- No --> M4
    S0 -- Yes --> S1
    S1 --> S2
    %% GUI AND BUTTONS
    S2 -- GUI --> H3
    H3 -- Yes --> H4
    H3 -- No --> H5
    S2 -- Physical buttons --> H5
    H4 --> U2
    H5 --> U2
    U2 --> S3
    H5 --> S4
    S4 --> S5
    S5 -- No --> S6
    S6 -- No --> H5
    S6 -- Yes --> S7
    S7 --> S19
    S5 -- Yes --> S8
    H4 --> S8
    %% MOBILE SHARED VALIDATION
    S2 -- Mobile API --> API4
    API4 --> S8
    %% CREDENTIAL VALIDATION
    S8 <-->|Query credentials| D1
    S8 --> S9
    S9 -- No --> R4
    S9 -- Yes --> S10
    S10 -- No --> R3
    S10 -- Yes --> S15
    %% FACIAL RECOGNITION
    S2 -- Facial recognition --> U3
    U3 --> H6
    H6 --> S11
    S11 <-->|Compare facial embeddings| D2
    S11 --> S12
    S12 -- No --> R3
    S12 -- Yes --> S13
    S13 <-->|Query user permissions| D1
    S13 --> S14
    S14 -- No --> R4
    S14 -- Yes --> S15
    %% ROLE AND PERMISSION VALIDATION
    S15 -- Yes --> R1
    S15 -- No --> R2
    %% ACCESS RESULTS
    R1 --> S16
    R2 --> S16
    R3 --> S16
    R4 --> S17
    S16 --> D3
    S16 --> S18
    S17 --> S18
    %% MOBILE RESPONSE
    S18 --> API7
    API7 --> M3
    M3 --> M5
    %% PHYSICAL FEEDBACK
    S18 --> H7
    H7 -->|Authorized only| H8
    H8 --> H9
    H7 -->|Denied or error| S19
    H9 --> S19
    %% FACIAL ENROLLMENT
    S2 -- Facial enrollment --> EN1
    EN1 -- No --> EN9
    EN1 -- Yes --> EN2
    EN2 --> H6
    EN2 --> EN3
    EN3 --> EN4
    EN4 -- No --> EN2
    EN4 -- Yes --> EN5
    EN5 --> EN6
    EN6 --> D2
    EN6 --> EN7
    EN7 -- Yes --> EN8
    EN7 -- No --> EN9
    EN8 --> S19
    EN9 --> S19
    %% RETURN TO STANDBY
    S19 --> H10
    H10 --> H1
    ```