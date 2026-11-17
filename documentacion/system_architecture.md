```mermaid
flowchart LR
    %% USER INTERACTION
    subgraph USER["User Interaction"]
        U1[General User]
        U2[Administrator]
        U3[Technical Service]
    end
    %% MOBILE APPLICATION
    subgraph MOBILE["Mobile Application"]
        APP[Mobile Access Application]
    end
    %% HARDWARE LAYER
    subgraph HW["Raspberry Pi Hardware"]
        PIR[PIR Sensor]
        BTN[Physical Buttons]
        CAM[Camera]
        MON[Monitor]
        LED[Green / Red LEDs]
        BUZ[Buzzer]
        SPK[Speaker]
        MOT[Access Motor]
    end
    %% LOCAL SOFTWARE LAYER
    subgraph SW["Local Software Modules - Raspberry Pi"]
        CORE[Main System Controller]
        GUI[Python GUI]
        INPUT[Physical Input Capture Module]
        FACE[Local Facial Recognition Module]
        ENROLL[Facial Enrollment Module]
        API[Local HTTPS API Service]
        SESSION[Mobile Login and Session Authentication]
        GATE[Presence and Operation Control]
        AUTH[Shared Credential Validation]
        PERM[Role and Permission Validation]
        ACCESS[Access Decision Module]
        ADMIN[Administrator Management Module]
        FEEDBACK[Feedback Controller]
        MOTORCTRL[Motor Controller]
        LOGGER[Access Logging Module]
    end
    %% LOCAL DATA LAYER
    subgraph DATA["Local Data Layer"]
        DB[(MySQL Database)]
        USERS[(Users / Password Hashes / Roles / Permissions)]
        BIO[(Local Biometric Data)]
        LOGS[(Access Attempt Logs)]
    end
    %% USER INTERACTION
    U1 -->|Approaches access point| PIR
    U1 -->|GUI credentials| MON
    U1 -->|Physical input| BTN
    U1 -->|Facial identification| CAM
    U1 -->|Mobile login and access request| APP
    U2 -->|User management and enrollment| MON
    U3 -->|Authentication according to permissions| MON
    U3 -->|Mobile authentication| APP
    %% HARDWARE CONNECTIONS
    PIR -->|Presence detected| CORE
    PIR -->|Presence status| GATE
    CORE -->|Coordinate access operations| GATE
    CORE -->|Enable local interface| GUI
    MON <--> GUI
    GUI -->|Access credentials| GATE
    BTN -->|Button inputs| INPUT
    INPUT -->|Captured credentials| GATE
    CAM -->|Live facial capture| FACE
    CAM -->|Enrollment capture| ENROLL
    FACE -->|Identified user or unknown face| GATE
    %% MOBILE COMMUNICATION
    APP -->|Encrypted and authenticated local connection| API
    API -->|Mobile login| SESSION
    SESSION -->|Verify login credentials| AUTH
    AUTH -->|Login verification result| SESSION
    SESSION -->|Login result| API
    API -->|Mobile access request| GATE
    GATE -->|Check PIR and exclusive operation| AUTH
    API -->|Presence availability and access result| APP
    %% SHARED ACCESS VALIDATION
    AUTH <-->|Query user and password hash| DB
    AUTH -->|Validated user identity| PERM
    PERM <-->|Check role and permissions| DB
    PERM --> ACCESS
    %% ACCESS DECISION
    ACCESS -->|Authorized / Without permission / Unrecognized / System error| API
    ACCESS -->|Access result| GUI
    ACCESS --> FEEDBACK
    ACCESS --> LOGGER
    %% ADMINISTRATION
    GUI -->|Administrator operations| ADMIN
    ADMIN -->|Manage users, roles, and permissions| DB
    ADMIN -->|Start authorized enrollment| ENROLL
    ENROLL -->|Store biometric samples linked to user| DB
    %% DATABASE STRUCTURE
    DB --> USERS
    DB --> BIO
    DB --> LOGS
    LOGGER -->|User, method, result, date, and time| DB
    %% PHYSICAL FEEDBACK
    FEEDBACK --> LED
    FEEDBACK --> BUZ
    FEEDBACK --> SPK
    %% MOTOR CONTROL
    ACCESS -->|Authorized only| MOTORCTRL
    MOTORCTRL -->|Open and return after 3 seconds| MOT
    %% USER FEEDBACK
    LED -->|Visual access status| U1
    BUZ -->|Status and failure tones| U1
    SPK -->|Access granted audio| U1
    MOT -->|Physical access opening| U1
   ```