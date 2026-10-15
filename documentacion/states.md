```mermaid
flowchart TD
    A([Start]) --> B[Initialize system]
    B --> C[/Emit system-ready sound/]
    C --> D[Standby state]
    D --> E[/Wait for presence detection through PIR sensor/]
    E --> F{Person detected?}
    F -- No --> E
    F -- Yes --> G[Presence detected]
    G --> H{Operation type?}
    H -- Access attempt --> I{Authentication method?}
    H -- New user enrollment --> EN1{Administrator authorized?}
    %% GUI AUTHENTICATION
    I -- Graphical interface --> J[/Capture user ID and passcode through GUI/]
    J --> O[Access data captured]
    %% PHYSICAL BUTTON AUTHENTICATION
    I -- Physical buttons --> K[/Capture user ID and passcode through buttons/]
    I -- GUI unavailable --> K
    K --> L{Capture complete?}
    L -- No --> M{More than 4 seconds without input?}
    M -- No --> K
    M -- Yes --> N[Clear input buffer]
    N --> N1[Discard captured data]
    N1 --> D
    L -- Yes --> O
    %% FACIAL AUTHENTICATION
    I -- Facial recognition --> FR1[/Capture live facial image/]
    FR1 --> FR2[Local facial identification state]
    FR2 --> FR3{Registered face identified?}
    FR3 -- No --> FR4[Unknown face state]
    FR4 --> FR5[/Turn on red LED/]
    FR5 --> FR6[/Emit 3 short buzzer tones/]
    FR6 --> FR7[/Display access denied/]
    FR7 --> T[Log access attempt]
    FR3 -- Yes --> FR8[Face recognized state]
    FR8 --> FR9[Associate face with local user record]
    FR9 --> Q[Query role and permissions]
    %% DATABASE VALIDATION
    O --> P[(MySQL Database)]
    P --> Q[Query user, passcode, role, and permissions]
    Q --> R{Database query successful?}
    R -- No --> S[Failure state]
    S --> S1[/Emit one long buzzer tone/]
    S1 --> T
    R -- Yes --> V{User recognized and information correct?}
    V -- No --> W[Denied state]
    W --> W1[/Turn on red LED/]
    W1 --> W2[/Emit 3 short buzzer tones/]
    W2 --> W3[/Display access denied/]
    W3 --> T
    V -- Yes --> X[Identify user role]
    X --> Y{Do role and permissions authorize access?}
    %% PERMISSION RESULT
    Y -- No --> Z[No-permission state]
    Z --> Z1[/Turn on red LED/]
    Z1 --> Z2[/Emit 3 short buzzer tones/]
    Z2 --> Z3[/Display user without permission/]
    Z3 --> T
    Y -- Yes --> AA[Authorized state]
    AA --> AA1[/Turn on green LED/]
    AA1 --> AA2[/Emit 3 short buzzer tones/]
    AA2 --> AA3[/Display access granted/]
    AA3 --> AA4[/Play "Access granted" audio message/]
    AA4 --> AB[Activate motor]
    AB --> AC[Access open state]
    AC --> AD[Wait 3 seconds]
    AD --> AE[Return motor to resting position]
    AE --> T
    %% USER ENROLLMENT
    EN1 -- No --> EN2[Enrollment denied state]
    EN2 --> EN3[/Display authorization denied/]
    EN3 --> D
    EN1 -- Yes --> EN4[/Capture new user's face live/]
    EN4 --> EN5[Generate biometric representation locally]
    EN5 --> EN6[Associate biometric data with user record and permissions]
    EN6 --> EN7[Enrollment completed state]
    EN7 --> EN8[/Display successful enrollment confirmation/]
    EN8 --> D
    %% LOG AND RESET
    T --> U[(Access attempt logs)]
    U --> AF[Clear operation data]
    AF --> D
    ```