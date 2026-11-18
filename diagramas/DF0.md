```mermaid
flowchart LR
    U[General User]
    A[Administrator]
    ST[Technical Service]
    MA[Mobile Application]
    S["Local Access Control System"]
    U -->|Identification and passcode via GUI or physical buttons| S
    U -->|Facial capture for enrollment or identification| S
    U -->|Presence detected through PIR sensor| S
    U -->|ID and passcode or Android biometrics, then request access| MA
    S -->|PIR presence status| MA
    MA -->|Local HTTPS sign-in and session-backed access request| S
    S -->|Authorized, no permission, unrecognized, or system error| MA
    MA -->|Display access result or technical failure| U
    S -->|Access validation result| U
    S -->|LED, buzzer, and audio feedback| U
    S -->|Motor activation when access is authorized| U
    A -->|Manage users, passcodes, roles, and permissions| S
    A -->|Manage facial enrollment| S
    S -->|Confirmation of changes and enrollment| A
    ST -->|Authentication according to assigned permissions| S
    S -->|Access validation result| ST
    ```
