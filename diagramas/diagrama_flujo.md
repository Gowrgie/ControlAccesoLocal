```mermaid
flowchart TD
    A([Start]) --> B[Initialize system]
    B --> C[/Emit system-ready sound/]
    C --> D[Standby state]
    %% LOCAL ACCESS
    D --> E[/Wait for PIR presence detection/]
    E --> F{Person detected?}
    F -- No --> E
    F -- Yes --> G[/Enable identification interfaces/]
    G --> H{Authentication method?}
    H -- GUI --> I[/Enter user ID and passcode through GUI/]
    H -- Physical buttons --> J[/Enter user ID and passcode through buttons/]
    H -- Facial recognition --> FR1[/Capture live facial image/]
    %% MOBILE ACCESS
    D --> M1[/Receive mobile login and access request/]
    M1 --> M2{Secure and authenticated local API connection?}
    M2 -- No --> M3[/Reject insecure request/]
    M3 --> Z
    M2 -- Yes --> M4{PIR presence detected?}
    M4 -- No --> M5[/Inform app that access is unavailable/]
    M5 --> Z
    M4 -- Yes --> M6[/Receive mobile user ID and passcode/]
    %% OPERATION CONTROL
    I --> OP
    J --> OP
    FR1 --> OP
    M6 --> OP
    OP{System available for a new operation?}
    OP -- No --> BUSY[/Return system busy response/]
    BUSY --> Z
    OP -- Yes --> LOCK[Reserve access operation]
    LOCK --> METHOD{Selected authentication method?}
    METHOD -- Credentials --> CAP{Physical button capture?}
    METHOD -- Facial --> FR2
    %% PHYSICAL BUTTON FLOW
    CAP -- Yes --> K{Capture complete?}
    K -- No --> L{More than 4 seconds without input?}
    L -- No --> J
    L -- Yes --> N[Clear input buffer and discard data]
    N --> Z
    K -- Yes --> O[Prepare captured credentials]
    CAP -- No --> O
    %% SHARED CREDENTIAL VALIDATION
    O --> P[Query user, passcode hash, role and permissions in MySQL]
    P --> Q{Database query successful?}
    Q -- No --> R4[System error]
    Q -- Yes --> S{Registered user and correct passcode?}
    S -- No --> R3[Unrecognized]
    S -- Yes --> U{Role and permissions authorize access?}
    %% FACIAL RECOGNITION
    FR2[Perform facial identification locally]
    FR2 --> FR3{Registered face identified?}
    FR3 -- No --> R3
    FR3 -- Yes --> FR4[Retrieve linked user and permissions]
    FR4 --> FR5{Database query successful?}
    FR5 -- No --> R4
    FR5 -- Yes --> U
    %% AUTHORIZATION RESULTS
    U -- No --> R2[Without permission]
    U -- Yes --> R1[Authorized]
    %% ACCESS LOGGING
    R1 --> LOG[Log access attempt]
    R2 --> LOG
    R3 --> LOG
    R4 --> LOG2[Log failure if database is available]
    LOG --> DB[(MySQL access logs)]
    DB --> RESULT{Access result?}
    LOG2 --> RESULT
    %% AUTHORIZED ACCESS
    RESULT -- Authorized --> W[/Return authorized result to requesting interface/]
    W --> W1[/Turn on green LED and emit 3 short tones/]
    W1 --> W2[/"Play Access granted audio"/]
    W2 --> X[Activate opening motor]
    X --> X1[Wait 3 seconds]
    X1 --> X2[Return motor to resting position]
    X2 --> Z
    %% WITHOUT PERMISSION
    RESULT -- Without permission --> V[/Display or return insufficient permissions/]
    V --> V1[/Turn on red LED and emit 3 short tones/]
    V1 --> Z
    %% UNRECOGNIZED
    RESULT -- Unrecognized --> T[/Display or return access denied/]
    T --> T1[/Turn on red LED and emit 3 short tones/]
    T1 --> Z
    %% SYSTEM ERROR
    RESULT -- System error --> ER[/Display or return technical failure/]
    ER --> ER1[/Emit one long buzzer tone/]
    ER1 --> Z
    %% USER ENROLLMENT
    D --> EN0[/Administrator requests facial enrollment/]
    EN0 --> EN1{Administrator authorized?}
    EN1 -- No --> EN2[/Display authorization denied/]
    EN2 --> Z
    EN1 -- Yes --> EN3{System available?}
    EN3 -- No --> BUSY
    EN3 -- Yes --> EN4[Reserve enrollment operation]
    EN4 --> EN5[/Capture facial samples with camera/]
    EN5 --> EN6[Validate image quality and facial poses]
    EN6 --> EN7{Capture requirements satisfied?}
    EN7 -- No --> EN5
    EN7 -- Yes --> EN8[Generate biometric representations locally]
    EN8 --> EN9[Associate facial data with user record]
    EN9 --> EN10[(Local biometric database)]
    EN10 --> EN11{Enrollment saved successfully?}
    EN11 -- Yes --> EN12[/Display enrollment confirmation/]
    EN11 -- No --> EN13[/Display enrollment error/]
    EN12 --> Z
    EN13 --> Z
    %% RESET
    Z[Return to standby state]
    Z --> Z1[Release reserved operation if active]
    Z1 --> Z2[Clear temporary data and reset indicators]
    Z2 --> C
    ```