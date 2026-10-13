```mermaid
flowchart LR
    U[General User]
    A[Administrator]
    ST[Technical Service]
    S["Local Access Control System"]
    U -->|Identification and passcode via GUI or physical buttons| S
    U -->|Facial capture for enrollment or identification| S
    S -->|Access validation result| U
    S -->|LED, buzzer, and audio feedback| U
    S -->|Motor activation when access is authorized| U
    A -->|Manage users, passcodes, roles, and permissions| S
    A -->|Manage user enrollment| S
    S -->|Confirmation of changes and enrollment| A
    ST -->|Authentication according to assigned permissions| S
    S -->|Access validation result| ST
    ```