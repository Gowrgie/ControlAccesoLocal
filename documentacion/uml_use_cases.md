```mermaid
flowchart LR
    %% EXTERNAL ACTORS
    U["Registered User"]
    API["Raspberry Pi Local API"]
    %% MOBILE APPLICATION BOUNDARY
    subgraph APP["Mobile Access Application"]
        direction TB
        UC1(["Sign in"])
        PASS(["Sign in with ID and passcode"])
        BIO(["Sign in with Android biometrics"])
        LINK(["Link this phone"])
        UC2(["Check PIR presence"])
        UC3(["Request access"])
        UC4(["Use secure local connection"])
        UC5(["View access result"])
        UC6(["View technical failure"])
        UC7(["Return to standby"])
    end
    %% USER ASSOCIATIONS
    U --- UC1
    U --- UC3
    U --- UC5
    %% USE CASE RELATIONSHIPS
    PASS -->|specializes| UC1
    BIO -->|specializes| UC1
    LINK -.->|extend| PASS
    UC1 -.->|include| UC4
    UC3 -.->|include| UC2
    UC3 -.->|include| UC4
    UC3 -.->|include| UC5
    UC6 -.->|extend| UC5
    UC5 -.->|include| UC7
    %% EXTERNAL SYSTEM INTERACTIONS
    UC1 --- API
    UC2 --- API
    UC3 --- API
    UC4 --- API
    UC5 --- API
    BIO --- ANDROID["Android biometric service"]
    ```
