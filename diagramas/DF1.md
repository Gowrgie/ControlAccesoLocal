```mermaid
flowchart LR
    U[General User]
    ST[Technical Service]
    A[Administrator]
    E1[/User ID and passcode through GUI/]
    E2[/User ID and passcode through physical buttons/]
    E3[/Live facial capture/]
    P1[Capture access data]
    P2[Validate entered data]
    P3[Query access information]
    P4[Evaluate user, passcode, role, and permissions]
    P5[Perform local facial identification]
    P6[Associate facial data with local user record]
    P7[Generate access result]
    P8[Log access attempt]
    P9[Update user access information]
    P10[Enroll new user facial data]
    D1[(Captured access data)]
    D2[(MySQL Database)]
    D3[(Access attempt logs)]
    D4[(Local biometric data)]
    C1{Is database query successful?}
    C2{Is facial identification successful?}
    C3{Is access authorized by role and permissions?}
    S1[/Validation result/]
    S2[/Green or red LED/]
    S3[/Three short buzzer tones/]
    S4[/"Access granted" audio message/]
    S5[/Motor opening command/]
    S6[/Update confirmation/]
    S7[/Long system-failure tone/]
    S8[/Enrollment confirmation/]
    U --> E1
    U --> E2
    U --> E3
    ST --> E1
    ST --> E2
    ST --> E3
    A --> E1
    A --> E2
    A --> E3
    E1 --> P1
    E2 --> P1
    P1 --> D1
    D1 --> P2
    P2 --> P3
    P3 --> D2
    D2 -->|User, passcode, role, and permissions| P4
    P4 --> C1
    C1 -- No --> S7
    S7 --> S1
    C1 -- Yes --> C3
    E3 --> P5
    D4 --> P5
    P5 --> C2
    C2 -- No --> P7
    C2 -- Yes --> P6
    P6 --> D2
    D2 -->|Role and permissions| C3
    C3 -- No --> P7
    C3 -- Yes --> P7
    P7 --> S1
    P7 --> S2
    P7 --> S3
    S1 --> U
    S1 --> ST
    S1 --> A
    S2 --> U
    S2 --> ST
    S2 --> A
    S3 --> U
    S3 --> ST
    S3 --> A
    C3 -- Yes --> S4
    S4 --> S5
    S4 --> U
    S4 --> ST
    S4 --> A
    P7 --> P8
    P8 --> D3
    A -->|Manage users, passcodes, roles, and permissions| P9
    P9 --> D2
    P9 --> S6
    S6 --> A
    A -->|Register new user| P10
    P10 --> E3
    E3 --> D4
    P10 --> P6
    P10 --> S8
    S8 --> A
    ```
