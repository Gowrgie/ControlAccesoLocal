```mermaid
flowchart TD
    A([Start]) --> B[Initialize system]
    B --> C[/Emit system-ready sound/]
    C --> D[/Wait for presence detection through PIR sensor/]
    D --> E{Person detected?}
    E -- No --> D
    E -- Yes --> F[/Display identification screen/]
    F --> G{Operation type?}
    G -- Access attempt --> H{Authentication method?}
    G -- New user enrollment --> EN1{Administrator authorized?}
    H -- Graphical interface --> I[/Capture user ID and passcode through GUI/]
    H -- Physical buttons --> J[/Capture user ID and passcode through buttons/]
    H -- Facial recognition --> FR1[/Capture live facial image/]
    %% PHYSICAL BUTTON FLOW
    J --> K{Capture complete?}
    K -- No --> L{More than 4 seconds without input?}
    L -- No --> J
    L -- Yes --> M[Clear input buffer]
    M --> N[Discard entered data]
    N --> Z[Return to standby state]
    K -- Yes --> O[Consolidate captured data]
    I --> O
    %% USER AND PASSCODE VALIDATION
    O --> P[Query user, passcode, role, and permissions in MySQL]
    P --> Q{Database query successful?}
    Q -- No --> R[/Indicate system failure/]
    R --> R1[/Emit one long buzzer tone/]
    R1 --> R2[Log database failure]
    R2 --> Z
    Q -- Yes --> S{User recognized and information correct?}
    S -- No --> T[/Turn on red LED/]
    T --> T1[/Emit 3 short buzzer tones/]
    T1 --> T2[/Display access denied/]
    T2 --> T3[Log denied attempt]
    T3 --> Z
    S -- Yes --> U{Do role and permissions authorize access?}
    %% FACIAL RECOGNITION FLOW
    FR1 --> FR2[Perform facial identification locally]
    FR2 --> FR3{Registered face identified?}
    FR3 -- No --> FR4[/Turn on red LED/]
    FR4 --> FR5[/Emit 3 short buzzer tones/]
    FR5 --> FR6[/Display access denied/]
    FR6 --> FR7[Log unknown-face attempt]
    FR7 --> Z
    FR3 -- Yes --> FR8[Associate face with local user record]
    FR8 --> FR9[Query role and permissions]
    FR9 --> U
    %% PERMISSION VALIDATION
    U -- No --> V[/Turn on red LED/]
    V --> V1[/Emit 3 short buzzer tones/]
    V1 --> V2[/Display user without permission/]
    V2 --> V3[Log attempt without permission]
    V3 --> Z
    U -- Yes --> W[/Turn on green LED/]
    W --> W1[/Emit 3 short buzzer tones/]
    W1 --> W2[/Display access granted/]
    W2 --> W3[/Play "Access granted" audio message/]
    W3 --> X[Activate opening motor]
    X --> X1[Wait 3 seconds]
    X1 --> X2[Return motor to resting position]
    X2 --> X3[Log authorized attempt]
    X3 --> 
    %% USER ENROLLMENT
    EN1 -- No --> EN2[/Display authorization denied/]
    EN2 --> Z
    EN1 -- Yes --> EN3[/Capture new user's face live/]
    EN3 --> EN4[Generate biometric representation locally]
    EN4 --> EN5[Associate biometric data with user record and permissions]
    EN5 --> EN6[/Display successful enrollment confirmation/]
    EN6 --> Z
    Z --> C
    ```