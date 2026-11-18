```mermaid
flowchart LR
    %% ACTORS
    U[General User]
    ST[Technical Service]
    A[Administrator]
    MA[Mobile Application]
    %% ACCESS INPUTS
    E1[/User ID and passcode through GUI/]
    E2[/User ID and passcode through physical buttons/]
    E3[/Live facial capture/]
    E4[/Mobile login and access request/]
    %% MOBILE API
    P1[Receive mobile request through local API]
    C1{Encrypted local connection?}
    ML[Verify passcode or linked-device signature]
    MS{Valid mobile session?}
    MK[(Linked Android public keys)]
    C2{PIR presence detected?}
    C3{Access operation available?}
    %% SHARED VALIDATION
    P2[Capture and prepare access data]
    P3[Query user, stored hash, role, and permissions]
    P4[Verify entered passcode against stored hash]
    P5[Perform local facial identification]
    P6[Query identified user's role and permissions]
    P7[Evaluate role and access permissions]
    P8[Generate access result]
    P9[Log access attempt]
    %% ADMINISTRATION AND ENROLLMENT
    P10[Update user access information]
    P11[Start guided facial enrollment]
    P12[Validate capture quality and generate facial embeddings]
    P13[Associate biometric samples with local user record]
    %% DATA STORES
    D1[(Temporary captured data)]
    D2[(MySQL users, password hashes, roles, and permissions)]
    D3[(Access attempt logs)]
    D4[(Local biometric data)]
    %% DECISIONS
    C4{Authentication method?}
    C5{Database query successful?}
    C6{User and passcode valid?}
    C7{Registered face identified?}
    C8{User query successful?}
    C9{Role and permissions allow access?}
    C10{Enrollment saved successfully?}
    %% ACCESS RESULTS
    R1[Authorized]
    R2[Without permission]
    R3[Unrecognized]
    R4[System error]
    %% OUTPUTS
    S1[/Access result to requesting interface/]
    S2[/Green LED and 3 short buzzer tones/]
    S3[/Red LED and 3 short buzzer tones/]
    S4[/"Access granted" audio message/]
    S5[/Motor opening and return to rest after 3 seconds/]
    S6[/Long system-failure tone/]
    S7[/Mobile request unavailable/]
    S8[/Secure connection rejected/]
    S9[/Update confirmation/]
    S10[/Enrollment confirmation/]
    S11[/Enrollment error/]
    %% ACTOR INPUTS
    U --> E1
    U --> E2
    U --> E3
    U --> E4
    ST --> E1
    ST --> E2
    ST --> E3
    ST --> E4
    A --> E1
    A --> E2
    A --> E3
    A --> E4
    %% MOBILE ACCESS FLOW
    E4 --> MA
    MA -->|Local network request| P1
    P1 --> C1
    C1 -- No --> S8
    S8 --> MA
    C1 -- Yes --> ML
    ML <-->|Link or look up device key| MK
    ML <-->|Query account| D2
    ML --> MS
    MS -- No --> S8
    MS -- Yes --> C2
    C2 -- No --> S7
    S7 --> MA
    C2 -- Yes --> MQ[Queue request and wait for its turn]
    MQ --> MP{Turn available before expiry with PIR still active?}
    MP -- No --> S7
    MP -- Yes --> P6

    %% OTHER ACCESS METHODS
    E1 --> C3
    E2 --> C3
    E3 --> C3

    %% ONE OPERATION AT A TIME
    C3 -- No --> S7
    C3 -- Yes --> C4
    C4 -- GUI or buttons --> P2
    C4 -- Facial recognition --> P5

    %% CREDENTIAL VALIDATION
    P2 --> D1
    D1 --> P3
    P3 <-->|User data query| D2
    P3 --> C5
    C5 -- No --> R4
    C5 -- Yes --> P4
    P4 --> C6
    C6 -- No --> R3
    C6 -- Yes --> P7
    %% FACIAL IDENTIFICATION
    P5 <-->|Compare facial embeddings| D4
    P5 --> C7
    C7 -- No --> R3
    C7 -- Yes --> P6
    P6 <-->|User role and permissions| D2
    P6 --> C8
    C8 -- No --> R4
    C8 -- Yes --> P7
    %% PERMISSION VALIDATION
    P7 --> C9
    C9 -- Yes --> R1
    C9 -- No --> R2
    %% STANDARDIZED RESULTS
    R1 --> P8
    R2 --> P8
    R3 --> P8
    R4 --> P8
    P8 --> S1
    S1 --> U
    S1 --> ST
    S1 --> A
    S1 --> MA
    %% ACCESS LOGGING
    P8 --> P9
    P9 -->|Save attempt when database is available| D3
    %% PHYSICAL FEEDBACK
    R1 --> S2
    R1 --> S4
    S4 --> S5
    R2 --> S3
    R3 --> S3
    R4 --> S6
    %% ADMINISTRATOR MANAGEMENT
    A -->|Manage users, passcodes, roles, and permissions| P10
    P10 --> D2
    P10 --> S9
    S9 --> A
    %% FACIAL ENROLLMENT
    A -->|Register facial data for a user| P11
    P11 --> P12
    P12 --> P13
    P13 --> D4
    P13 -->|Link samples to user ID| D2
    P13 --> C10
    C10 -- Yes --> S10
    C10 -- No --> S11
    S10 --> A
    S11 --> A
    ```
