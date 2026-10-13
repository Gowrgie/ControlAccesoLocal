```mermaid
flowchart TD
    A([Start])
    A --> B[Initialize Raspberry Pi, GPIO, PIR, LEDs, buzzer, audio, camera, and motor]
    B --> C[Initialize MySQL database connection]
    C --> D[/Emit system-ready sound/]
    D --> E[/Wait for presence detection through PIR sensor/]
    E --> F{Person detected?}
    F -- No --> E
    F -- Yes --> G{System available for a new operation?}
    G -- No --> E
    G -- Yes --> H[/Display identification screen/]
    H --> I{Operation type?}
    I -- Access attempt --> J{Authentication method?}
    I -- New user enrollment --> EN1{Administrator authorized?}
    %% GUI AUTHENTICATION
    J -- Graphical interface --> K[/Capture user ID and passcode through GUI/]
    K --> L[Consolidate captured access data]
    %% PHYSICAL BUTTON AUTHENTICATION
    J -- Physical buttons --> M[/Capture user ID and passcode through buttons/]
    M --> N[GPIO detects button inputs]
    N --> O[Apply debounce control]
    O --> P[Register identifier and passcode]
    P --> Q{Capture complete?}
    Q -- No --> R{More than 4 seconds without input?}
    R -- No --> M
    R -- Yes --> S[Clear input buffer]
    S --> T[Discard captured data]
    T --> Z[Return to standby state]
    Q -- Yes --> L
    %% FACIAL AUTHENTICATION
    J -- Facial recognition --> FA1[/Capture live facial image/]
    FA1 --> FA2[Perform facial detection and identification locally]
    FA2 --> FA3{Registered face identified?}
    FA3 -- No --> FA4[/Turn on red LED/]
    FA4 --> FA5[/Emit 3 short buzzer tones/]
    FA5 --> FA6[/Display access denied/]
    FA6 --> FA7[Log unknown-face attempt]
    FA7 --> LOG[(Access attempt logs)]
    LOG --> Z
    FA3 -- Yes --> FA8[Associate identified face with local user record]
    FA8 --> DB[(MySQL Database)]
    DB --> FA9[Query user role and permissions]
    FA9 --> PERM{Do role and permissions authorize access?}
    %% PASSCODE DATABASE VALIDATION
    L --> DB
    DB --> U[Query user, passcode, role, and permissions]
    U --> V{Database query successful?}
    V -- No --> W[/Indicate system failure/]
    W --> W1[/Emit one long buzzer tone/]
    W1 --> W2[Log database failure]
    W2 --> LOG
    V -- Yes --> X{User recognized and passcode correct?}
    X -- No --> Y[/Turn on red LED/]
    Y --> Y1[/Emit 3 short buzzer tones/]
    Y1 --> Y2[/Display access denied/]
    Y2 --> Y3[Log denied attempt]
    Y3 --> LOG
    X -- Yes --> X1[Identify user role]
    X1 --> PERM
    %% ROLE AND PERMISSION VALIDATION
    PERM -- No --> AA[/Turn on red LED/]
    AA --> AA1[/Emit 3 short buzzer tones/]
    AA1 --> AA2[/Display user without permission/]
    AA2 --> AA3[Log attempt without permission]
    AA3 --> LOG
    PERM -- Yes --> AB[/Turn on green LED/]
    AB --> AB1[/Emit 3 short buzzer tones/]
    AB1 --> AB2[/Display access granted/]
    AB2 --> AB3[/Play "Access granted" audio message/]
    AB3 --> AC[Activate opening motor]
    AC --> AD[Wait 3 seconds]
    AD --> AE[Return motor to resting position]
    AE --> AF[Log authorized access attempt]
    AF --> LOG
    %% USER ENROLLMENT
    EN1 -- No --> EN2[/Display authorization denied/]
    EN2 --> Z
    EN1 -- Yes --> EN3[/Capture new user's face live/]
    EN3 --> EN4[Generate biometric representation locally]
    EN4 --> EN5[Associate biometric data with local user record and permissions]
    EN5 --> DB
    EN5 --> EN6[/Display successful enrollment confirmation/]
    EN6 --> Z
    %% RESET
    Z --> AG[/Turn off LEDs and finish active signals/]
    AG --> AH[Clear operation data]
    AH --> D
    ```