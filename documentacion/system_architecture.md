```mermaid
flowchart LR
    subgraph USER["User Interaction"]
        U1[General User]
        U2[Administrator]
        U3[Technical Service]
    end

    subgraph HW["Hardware - Raspberry Pi"]
        PIR[PIR Sensor]
        BTN[Physical Buttons]
        CAM[Camera]
        MON[Monitor]
        LED[Green / Red LEDs]
        BUZ[Buzzer]
        SPK[Speaker]
        MOT[Access Motor]
    end

    subgraph SW["Local Software Modules"]
        CORE[Main System Controller]

        GUI[Python GUI]
        INPUT[Input Capture Module]
        FACE[Local Facial Recognition Module]
        ENROLL[Facial Enrollment Module]

        AUTH[Authentication Module]
        PERM[Role and Permission Validation]
        ACCESS[Access Decision Module]

        FEEDBACK[Feedback Controller]
        MOTORCTRL[Motor Controller]
        LOGGER[Access Logging Module]
    end

    subgraph DATA["Local Data Layer"]
        DB[(MySQL Database)]
        USERS[(Users / Passcodes / Roles / Permissions)]
        BIO[(Local Biometric Data)]
        LOGS[(Access Attempt Logs)]
    end

    U1 -->|Approaches access point| PIR
    U1 -->|User ID and passcode| MON
    U1 -->|Physical input| BTN
    U1 -->|Face capture| CAM
    U2 -->|User management and enrollment| MON
    U3 -->|Authentication according to permissions| MON

    PIR -->|Presence detected| CORE
    MON <--> GUI
    GUI --> INPUT
    BTN -->|Button inputs| INPUT
    CAM -->|Live facial capture| FACE
    CAM -->|Enrollment capture| ENROLL

    INPUT --> AUTH
    FACE --> AUTH
    ENROLL -->|Biometric representation| BIO
    ENROLL -->|Associate with local user| DB
    AUTH -->|Query credentials / user| DB
    AUTH --> PERM
    PERM -->|Check role and permissions| DB
    PERM --> ACCESS
    FACE -->|Identified local user| PERM
    ACCESS -->|Authorized / denied / failure| FEEDBACK
    ACCESS --> LOGGER

    DB --> USERS
    DB --> BIO
    DB --> LOGS
    LOGGER -->|Date, time, user, mechanism, result| LOGS

    FEEDBACK --> LED
    FEEDBACK --> BUZ
    FEEDBACK --> SPK
    ACCESS -->|Authorized only| MOTORCTRL
    MOTORCTRL --> MOT

    LED -->|Access status| U1
    BUZ -->|Status / failure tones| U1
    SPK -->|"Access granted"| U1
    MOT -->|Physical access opening| U1
   ```