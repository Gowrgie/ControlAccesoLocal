# Traceability

This document links the system requirements with the Jira tasks, project changes, and available validation evidence.

## Functional Requirements

| Requirement | Jira Key | PR / Change | Validation Evidence |
|---|---|---|---|
| FR-01 | LAC-55, LAC-58 | `access_flow.py`, `access_logic.py` | The system captures access data, validates it against local information, and returns an authorized or denied result. |
| FR-02 | LAC-55, LAC-58 | `access_flow.py` | The physical flow captures a user identifier and a passcode of 4 to 6 inputs. |
| FR-03 | LAC-55, LAC-57 | `hardware.py` | Green and red LEDs indicate authorized and denied access results. |
| FR-04 | LAC-55, LAC-57 | `access_flow.py`, `headless_mode.py` | Captured data is cleared after each operation, allowing a new access attempt. |
| FR-05 | LAC-55, LAC-57 | `access_flow.py` | An incomplete physical capture is discarded when more than 4 seconds pass without input. |
| FR-06 | LAC-55, LAC-57 | `hardware.py`, `headless_mode.py` | The buzzer indicates when the system returns to standby and is ready again. |
| FR-07 | LAC-55, LAC-57 | `hardware.py` | The system provides buzzer tones for access results and a different sound for system failures. |
| FR-08 | LAC-55, LAC-57 | `hardware.py`, system flow diagrams | The PIR sensor detects presence before enabling an access operation. |
| FR-09 | LAC-29, LAC-55 | `gui.py`, wireframes | The Python GUI supports user identification, passcode entry, and access result display. |
| FR-10 | LAC-29, LAC-55 | `gui.py` | The graphical interface is designed for the monitor connected to the Raspberry Pi. |
| FR-11 | LAC-53, LAC-55, LAC-66 | `db_conexion.py`, `database.py` | MySQL stores user information and access attempts, including the authentication method and result. |
| FR-12 | LAC-55, LAC-65 | `db_conexion.py`, database schema | Users are associated with roles and permissions used during access validation. |
| FR-13 | LAC-55, LAC-65, LAC-67 | `access_logic.py`, `db_conexion.py` | The system distinguishes authorized access, missing permissions, invalid users, and system errors. |
| FR-14 | LAC-55, LAC-57 | `access_flow.py`, `headless_mode.py` | Physical buttons use the same access validation logic as the graphical interface. |
| FR-15 | LAC-55, LAC-57 | `headless_mode.py` | Physical-button authentication can operate without the graphical interface. |
| FR-16 | LAC-55, LAC-57 | `audio.py` | Authorized access plays the "Access granted" audio message. |
| FR-17 | LAC-55, LAC-57 | `hardware.py`, system diagrams | Authorized access activates the motor and returns it to its resting position after 3 seconds. |
| FR-18 | LAC-55, LAC-57 | `access_flow.py`, `headless_mode.py` | The system clears the operation data and returns to standby after each access attempt. |
| FR-19 | LAC-47, LAC-51, LAC-65 | `registrar_rostro.py`, `calidad_captura.py`, `camera.py`, `database.py` | Facial enrollment guides the user through five captures, checks image quality, and stores the facial samples in MySQL. |
| FR-20 | LAC-47, LAC-51, LAC-67 | `reconocer_rostro.py`, `calidad_captura.py`, `camera.py` | Facial detection and identification use YuNet and SFace locally, without cloud recognition services. |
| FR-21 | LAC-53, LAC-65, LAC-71 | `registrar_rostro.py`, `database.py`, `db_conexion.py` | Each facial sample is stored with a user ID, linking biometric data to the corresponding local user and permissions. |
| FR-22 | LAC-65, LAC-67 | `reconocer_rostro.py`, `access_flow.py`, `access_logic.py`, `db_conexion.py` | After identifying a face, the system checks the user's permissions and determines whether access is allowed. |
| FR-23 | LAC-67 | `reconocer_rostro.py`, `access_logic.py`, `db_conexion.py` | Unknown faces are rejected when no stored facial sample meets the recognition threshold. |

## Non-Functional Requirements

| Requirement | Jira Key | PR / Change | Validation Evidence |
|---|---|---|---|
| NFR-01 | LAC-55 | `hardware.py`, `access_flow.py` | Button inputs include debounce handling to prevent duplicate readings. |
| NFR-02 | LAC-53, LAC-65, LAC-71 | `database.py`, `db_conexion.py`, database scripts | User information and biometric records are stored locally with controlled database operations. |
| NFR-03 | LAC-55 | `access_flow.py`, `access_logic.py` | Access validation is processed locally. The 1-second response limit still requires a measured test. |
| NFR-04 | LAC-55 | `hardware.py`, `gui.py` | PIR detection is integrated into the access flow. The 1-second detection limit requires hardware testing. |
| NFR-05 | LAC-29 | `gui.py`, wireframes | The interface provides simple screens for identification and access results. |
| NFR-06 | LAC-55, LAC-65 | `db_conexion.py` | Database failures are handled separately from normal access denial. The 2-second query limit requires verification. |
| NFR-07 | LAC-55, LAC-57 | `headless_mode.py` | Physical buttons allow authentication without depending on the graphical desktop interface. |
| NFR-08 | LAC-55 | `audio.py` | The authorized-access audio is implemented. Its audibility at 1 meter requires physical testing. |
| NFR-09 | LAC-53, LAC-66 | `db_conexion.py` | Access attempts are stored in MySQL for later consultation, separately from the user interfaces. |
| NFR-10 | LAC-55 | `gui.py`, `access_flow.py` | The access flow controls operations to avoid simultaneous authentication through different interfaces. |
| NFR-11 | LAC-47, LAC-51, LAC-55, LAC-67 | `reconocer_rostro.py`, `registrar_rostro.py`, `calidad_captura.py`, `camera.py`, `access_flow.py`, `access_logic.py`, `db_conexion.py` | Facial recognition, biometric comparison, database queries, and access decisions are processed locally without cloud services. |

## Documentation and Diagrams

| Jira Key | Change | Evidence |
|---|---|---|
| LAC-57 | Update documentation and diagrams | DF0, DF1, system flow, general flow, process, sequence, and states diagrams were updated in English. |
| LAC-58 | Translate requirements and add facial requirements | `Requirements.md` was translated to English and extended through FR-23 and NFR-11. |
| LAC-74 | Create system architecture diagram | `system_architecture.md` shows the interaction between hardware, software, database, facial recognition, and access control. |
| LAC-79 | Rebuild traceability in English with Jira keys | The traceability document was updated with Jira keys, current modules, and the latest requirements. |