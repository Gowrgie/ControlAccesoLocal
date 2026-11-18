```mermaid
flowchart TD
    %% SYSTEM INITIALIZATION
    A([Start]) --> B[Initialize system, hardware, database, and local API]
    B --> C[/Emit system-ready sound/]
    C --> D[Standby state]
    %% LOCAL PRESENCE DETECTION
    D --> E[/Monitor presence through PIR sensor/]
    E --> F{Person detected?}
    F -- No --> E
    F -- Yes --> G[Presence detected state]
    G --> SLOT{System available for a new operation?}
    %% MOBILE LOGIN
    D --> ML1[/Receive mobile login request/]
    ML1 --> ML2{Encrypted local API connection?}
    ML2 -- No --> ML3[Mobile connection rejected state]
    ML3 --> ML4[/Display connection error in mobile app/]
    ML4 --> D
    ML2 -- Yes --> ML5[Verify passcode or a signature from the linked Android device]
    ML5 --> ML6{Database query successful?}
    ML6 -- No --> ML7[Mobile login error state]
    ML7 --> ML8[/Display technical login error/]
    ML8 --> D
    ML6 -- Yes --> ML9{Valid sign-in for an active user?}
    ML9 -- No --> ML10[Mobile login denied state]
    ML10 --> ML11[/Display invalid credentials/]
    ML11 --> D
    ML9 -- Yes --> ML12[Mobile authenticated state]
    ML12 --> ML13[Mobile app waiting for presence]
    ML13 --> ML14{PIR presence confirmed by Raspberry Pi?}
    ML14 -- No --> ML13
    ML14 -- Yes --> ML15[/Send mobile access request through local API/]
    ML15 --> ML16{Session authenticated and connection secure?}
    ML16 -- No --> ML17[/Reject request and display technical error/]
    ML17 --> D
    ML16 -- Yes --> ML18{PIR still detects presence?}
    ML18 -- No --> ML19[/Display access request unavailable/]
    ML19 --> D
    ML18 -- Yes --> MQ[Mobile request queued]
    MQ --> MP{Turn available before expiry with PIR still active?}
    MP -- No --> ML19
    MP -- Yes --> MOB1
    %% SHARED OPERATION CONTROL
    SLOT -- No --> BUSY[System busy state]
    BUSY --> BUSY1[/Notify requesting interface/]
    BUSY1 --> D
    SLOT -- Yes --> LOCK[Reserve exclusive access operation]
    LOCK --> H{Operation type or authentication method?}
    H -- GUI --> GUI1[/Capture user ID and passcode through GUI/]
    H -- Physical buttons --> BTN1[/Capture user ID and passcode through buttons/]
    H -- Facial recognition --> FR1[/Capture live facial image/]
    H -- Facial enrollment --> EN1{Administrator authorized?}
    %% GRAPHICAL INTERFACE
    GUI1 --> O[Access data captured]
    %% PHYSICAL BUTTON AUTHENTICATION
    BTN1 --> BTN2[Apply debounce and register inputs]
    BTN2 --> BTN3{Capture complete?}
    BTN3 -- No --> BTN4{More than 4 seconds without input?}
    BTN4 -- No --> BTN1
    BTN4 -- Yes --> BTN5[Clear input buffer]
    BTN5 --> BTN6[Discard incomplete data]
    BTN6 --> RESET
    BTN3 -- Yes --> O
    %% MOBILE SESSION AUTHORIZATION
    MOB1[Resolve account from authenticated mobile session] --> FR9
    %% SHARED CREDENTIAL VALIDATION
    O --> Q[Query user, stored passcode hash, role, and permissions]
    Q -.-> DB[(Local MySQL Database)]
    Q --> R{Database query successful?}
    R -- No --> ERR[System error state]
    R -- Yes --> V{User recognized and passcode correct?}
    V -- No --> DENIED[Unrecognized state]
    V -- Yes --> PERM{Role and permissions authorize access?}
    %% FACIAL AUTHENTICATION
    FR1 --> FR2[Validate facial capture quality]
    FR2 --> FR3{Capture valid?}
    FR3 -- No --> FR4[/Request another facial capture/]
    FR4 --> FR1
    FR3 -- Yes --> FR5[Local facial identification state]
    FR5 -.-> BIO[(Local biometric data)]
    FR5 --> FR6{Registered face identified?}
    FR6 -- No --> UNKNOWN[Unknown face state]
    UNKNOWN --> DENIED
    FR6 -- Yes --> FR7[Face recognized state]
    FR7 --> FR8[Retrieve linked local user record]
    FR8 --> FR9[Query user role and permissions]
    FR9 --> FR10{Database query successful?}
    FR10 -- No --> ERR
    FR10 -- Yes --> PERM
    %% PERMISSION VALIDATION
    PERM -- No --> NOPER[Without permission state]
    PERM -- Yes --> AUTH[Authorized state]
    %% ACCESS RESULT LOGGING
    AUTH --> LOG[Register access attempt]
    NOPER --> LOG
    DENIED --> LOG
    LOG --> LOGDB[(Access attempt logs)]
    LOGDB --> RESULT[/Display result locally or return through mobile API/]
    ERR --> ERRLOG[Record failure if database is available]
    ERRLOG --> RESULT
    %% MOBILE RESPONSE
    RESULT -- Mobile request --> MOB2[/Display result and return mobile app to standby/]
    %% RESULT HANDLING
    RESULT --> DEC{Access result?}
    %% AUTHORIZED ACCESS
    DEC -- Authorized --> AA1[/Turn on green LED/]
    AA1 --> AA2[/Emit 3 short buzzer tones/]
    AA2 --> AA3[/Play "Access granted" audio message/]
    AA3 --> AB[Activate opening motor]
    AB --> AC[Access open state]
    AC --> AD[Wait 3 seconds]
    AD --> AE[Return motor to resting position]
    AE --> RESET
    %% WITHOUT PERMISSION
    DEC -- Without permission --> NP1[/Turn on red LED/]
    NP1 --> NP2[/Emit 3 short buzzer tones/]
    NP2 --> NP3[/Display insufficient permissions/]
    NP3 --> RESET
    %% UNRECOGNIZED USER OR FACE
    DEC -- Unrecognized --> DN1[/Turn on red LED/]
    DN1 --> DN2[/Emit 3 short buzzer tones/]
    DN2 --> DN3[/Display access denied/]
    DN3 --> RESET
    %% SYSTEM ERROR
    DEC -- System error --> ER1[Failure state]
    ER1 --> ER2[/Emit one long buzzer tone/]
    ER2 --> ER3[/Display technical failure/]
    ER3 --> RESET
    %% FACIAL ENROLLMENT
    EN1 -- No --> EN2[Enrollment denied state]
    EN2 --> EN3[/Display authorization denied/]
    EN3 --> RESET
    EN1 -- Yes --> EN4[Facial enrollment state]
    EN4 --> EN5[/Capture guided facial samples/]
    EN5 --> EN6[Validate image quality and facial poses]
    EN6 --> EN7{Required samples completed?}
    EN7 -- No --> EN5
    EN7 -- Yes --> EN8[Generate biometric representations locally]
    EN8 --> EN9[Associate samples with local user record]
    EN9 --> EN10[Store biometric samples in MySQL]
    EN10 --> EN11{Enrollment saved successfully?}
    EN11 -- No --> EN12[Enrollment error state]
    EN12 --> EN13[/Display enrollment failure/]
    EN13 --> RESET
    EN11 -- Yes --> EN14[Enrollment completed state]
    EN14 --> EN15[/Display successful enrollment confirmation/]
    EN15 --> RESET
    %% RESET AND RETURN TO STANDBY
    RESET[Release access operation]
    RESET --> AF[Clear temporary operation data]
    AF --> AG[/Turn off LEDs and finish active signals/]
    AG --> AH[/Emit standby sound/]
    AH --> D
    ```
