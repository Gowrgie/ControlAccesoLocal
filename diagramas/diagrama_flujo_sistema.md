```mermaid
flowchart TD
    A([Start])
    A --> B[Initialize Raspberry Pi, GPIO, PIR, LEDs, buzzer, audio, camera, and motor]
    B --> C[Initialize local MySQL connection]
    C --> C1[Start secure mobile API on the local network]
    C1 --> D[/Emit system-ready sound/]
    D --> E[Standby: monitor PIR sensor and mobile API]
    %% PRESENCE DETECTION
    E --> F{PIR detects a person?}
    F -- No --> E
    F -- Yes --> G[/Enable local identification interfaces/]
    G --> H{New access operation available?}
    %% MOBILE API REQUEST
    E --> MB1[/Receive mobile login and access request/]
    MB1 --> MB2{Encrypted and authenticated local connection?}
    MB2 -- No --> MB3[/Reject insecure request/]
    MB3 --> MB4[/Show technical error in mobile app/]
    MB4 --> Z
    MB2 -- Yes --> MB5{PIR currently detects presence?}
    MB5 -- No --> MB6[/Inform mobile app that access is unavailable/]
    MB6 --> Z
    MB5 -- Yes --> H
    %% SHARED OPERATION CONTROL
    H -- No --> H1[/Notify that system is busy/]
    H1 --> Z
    H -- Yes --> H2[Reserve exclusive access operation]
    H2 --> I{Requested operation or authentication method?}
    I -- GUI --> J{GUI and monitor available?}
    I -- Physical buttons --> K
    I -- Facial recognition --> FA1
    I -- Mobile API --> MOB1
    I -- Facial enrollment --> EN1
    %% GUI AUTHENTICATION
    J -- Yes --> J1[/Capture user ID and passcode through GUI/]
    J -- No --> K
    J1 --> L[Prepare captured access data]
    %% PHYSICAL BUTTON AUTHENTICATION
    K[/Capture user ID and passcode through buttons/]
    K --> M[GPIO detects button inputs]
    M --> N[Apply debounce control]
    N --> O[Register identifier and passcode]
    O --> P{Capture complete?}
    P -- No --> Q{More than 4 seconds without input?}
    Q -- No --> K
    Q -- Yes --> R[Clear input buffer]
    R --> S[Discard captured data]
    S --> Z
    P -- Yes --> L
    %% MOBILE AUTHENTICATION
    MOB1[/Receive mobile user ID and passcode through API/]
    MOB1 --> MOB2[Forward credentials to shared validation logic]
    MOB2 --> L
    %% SHARED CREDENTIAL VALIDATION
    L --> DB[(Local MySQL Database)]
    DB --> T[Query user, passcode hash, role, and permissions]
    T --> U{Query successful within 2 seconds?}
    U -- No --> ERR[System error result]
    U -- Yes --> V[Verify entered passcode against stored hash]
    V --> W{Registered user and correct passcode?}
    W -- No --> DENY[Unrecognized result]
    W -- Yes --> ROLE[Identify user role and permissions]
    ROLE --> PERM{Role and permissions authorize access?}
    %% LOCAL FACIAL RECOGNITION
    FA1[/Capture live facial image/]
    FA1 --> FA2[Check facial capture quality]
    FA2 --> FA3{Capture valid?}
    FA3 -- No --> FA4[/Request another facial capture/]
    FA4 --> FA1
    FA3 -- Yes --> FA5[Perform facial detection and identification locally]
    FA5 --> BIO[(Local biometric data)]
    BIO --> FA6{Registered face identified?}
    FA6 -- No --> DENY
    FA6 -- Yes --> FA7[Retrieve linked local user ID]
    FA7 --> FA8[Query user role and permissions from MySQL]
    FA8 --> FA9{Database query successful?}
    FA9 -- No --> ERR
    FA9 -- Yes --> PERM
    %% AUTHORIZATION DECISION
    PERM -- No --> NOPER[Without permission result]
    PERM -- Yes --> AUTH[Authorized result]
    %% AUTHORIZED RESULT
    AUTH --> AU1[/Display authorized result or return mobile API response/]
    AU1 --> AU2[/Turn on green LED/]
    AU2 --> AU3[/Emit 3 short buzzer tones/]
    AU3 --> AU4[/Play "Access granted" audio message/]
    AU4 --> AU5[Activate opening motor]
    AU5 --> AU6[Wait 3 seconds]
    AU6 --> AU7[Return motor to resting position]
    AU7 --> LOG1
    %% WITHOUT PERMISSION
    NOPER --> NP1[/Display without permission result or return mobile API response/]
    NP1 --> NP2[/Turn on red LED/]
    NP2 --> NP3[/Emit 3 short buzzer tones/]
    NP3 --> LOG1
    %% UNRECOGNIZED USER OR FACE
    DENY --> DN1[/Display unrecognized result or return mobile API response/]
    DN1 --> DN2[/Turn on red LED/]
    DN2 --> DN3[/Emit 3 short buzzer tones/]
    DN3 --> LOG1
    %% SYSTEM ERROR
    ERR --> ER1[/Display technical failure or return mobile API error/]
    ER1 --> ER2[/Indicate system failure/]
    ER2 --> ER3[/Emit one long buzzer tone/]
    ER3 --> LOG2
    %% ACCESS LOGGING
    LOG1[Log user, authentication method, result, date, and time]
    LOG1 --> LOGDB[(Access attempt logs)]
    LOGDB --> Z
    LOG2[Record system failure if database is available]
    LOG2 --> Z
    %% FACIAL ENROLLMENT
    EN1{Administrator authorized?}
    EN1 -- No --> EN2[/Display enrollment authorization denied/]
    EN2 --> Z
    EN1 -- Yes --> EN3[/Capture new user's face live/]
    EN3 --> EN4[Validate capture quality and required facial poses]
    EN4 --> EN5{Capture requirements satisfied?}
    EN5 -- No --> EN3
    EN5 -- Yes --> EN6[Generate biometric representations locally]
    EN6 --> EN7[Associate samples with local user ID]
    EN7 --> EN8[Store facial embeddings in MySQL]
    EN8 --> EN9{Enrollment saved successfully?}
    EN9 -- No --> EN10[/Display enrollment error/]
    EN10 --> Z
    EN9 -- Yes --> EN11[/Display successful enrollment confirmation/]
    EN11 --> Z
    %% RESET AND STANDBY
    Z[Return to standby state]
    Z --> AG[Release exclusive operation]
    AG --> AH[/Turn off LEDs and finish active signals/]
    AH --> AI[Clear temporary operation data]
    AI --> D
    ```