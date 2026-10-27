# Traceability

This document links the system requirements with the Jira tasks, project changes, and available validation evidence.

## Functional Requirements

| Requirement | Jira Key | PR / Change | Validation Evidence |
|---|---|---|---|
| FR-01 | LAC-55, LAC-58 | `access_flow.py`, `access_logic.py` | The system captures access data, validates it against local information, and returns an authorized or denied result. |
| FR-02 | LAC-55, LAC-58 | `access_flow.py` | The physical flow captures a user identifier and a passcode of 4 to 6 inputs. |
| FR-03 | LAC-55, LAC-57 | `hardware.py` | Green and red LEDs are used to indicate authorized and denied access results. |
| FR-04 | LAC-55, LAC-57 | `access_flow.py`, `headless_mode.py` | The capture state is cleared after an operation so the system can receive new data. |
| FR-05 | LAC-55, LAC-57 | `access_flow.py` | An incomplete physical capture is discarded when the input timeout is exceeded. |
| FR-06 | LAC-55, LAC-57 | `hardware.py`, `headless_mode.py` | The buzzer indicates when the system returns to standby and is ready again. |
| FR-07 | LAC-55, LAC-57 | `hardware.py` | The hardware provides result tones for access validation and a different response for system failures. |
| FR-08 | LAC-55, LAC-57 | `hardware.py`, system flow diagrams | The PIR sensor is used to detect presence before enabling an access operation. |
| FR-09 | LAC-29, LAC-55 | `gui.py`, wireframes | The Python GUI supports user identification, passcode entry, and access result display. |
| FR-10 | LAC-29, LAC-55 | `gui.py` | The graphical interface is designed for use on the Raspberry Pi display. |
| FR-11 | LAC-53, LAC-55, LAC-66 | Database scripts and access logging modules | MySQL stores user information and access attempts including the authentication mechanism and result. |
| FR-12 | LAC-55, LAC-65 | `db_conexion.py`, database schema | Users are associated with roles and permissions used during access validation. |
| FR-13 | LAC-55, LAC-65, LAC-67 | `access_logic.py`, `db_conexion.py` | The access logic distinguishes authorized access, missing permission, invalid users, and system errors. |
| FR-14 | LAC-55, LAC-57 | `access_flow.py`, `headless_mode.py` | Physical buttons reuse the system access flow instead of implementing a separate validation process. |
| FR-15 | LAC-55, LAC-57 | `headless_mode.py` | The physical-button mode can operate without the graphical desktop interface. |
| FR-16 | LAC-55, LAC-57 | `audio.py`, audio files | Authorized access plays the corresponding “Access granted” audio response. |
| FR-17 | LAC-55, LAC-57 | `hardware.py`, system diagrams | Authorized access activates the access motor and returns it to its resting position after the operation. |
| FR-18 | LAC-55, LAC-57 | `access_flow.py`, `headless_mode.py` | After each operation, the system clears its state and returns to standby. |
| FR-19 | LAC-47, LAC-51, LAC-65 | `camera.py`, facial registration modules | The project supports live facial capture and associates the enrolled biometric data with a local user. |
| FR-20 | LAC-47, LAC-51, LAC-67 | `face_engine.py`, facial recognition modules | Facial detection and identification are processed locally without a cloud recognition service. |
| FR-21 | LAC-53, LAC-65 | Biometric database table and `db_conexion.py` | Biometric information is linked to a local user record and its permissions. |
| FR-22 | LAC-65, LAC-67 | `face_engine.py`, `access_logic.py` | After facial identification, the system uses the linked user permissions to authorize or deny access. |
| FR-23 | LAC-67 | Facial recognition and access logic modules | An unknown or unregistered face produces a denied access result. |

## Non-Functional Requirements

| Requirement | Jira Key | PR / Change | Validation Evidence |
|---|---|---|---|
| NFR-01 | LAC-55 | `hardware.py`, `access_flow.py` | Physical button input includes debounce handling to avoid duplicate inputs. |
| NFR-02 | LAC-53, LAC-65, LAC-71 | Database scripts and access modules | User, role, permission, and biometric data are maintained in the local database with controlled operations. |
| NFR-03 | LAC-55 | Access validation modules | The validation flow is implemented locally. The 1-second response limit should be confirmed during system execution. |
| NFR-04 | LAC-55 | PIR handling in the hardware and GUI modules | Presence detection is integrated into the access flow. The 1-second limit should be confirmed during hardware testing. |
| NFR-05 | LAC-29 | GUI and wireframes | The interface uses a simple access flow with standby, identification, and result screens. |
| NFR-06 | LAC-55, LAC-65 | Database connection modules | MySQL queries are handled locally and database failures are treated separately from normal access denial. |
| NFR-07 | LAC-55, LAC-57 | `headless_mode.py` | Physical-button operation can run without the graphical interface or desktop environment. |
| NFR-08 | LAC-55 | `audio.py`, audio messages | The authorized-access audio is implemented. Audible distance should be confirmed during physical testing. |
| NFR-09 | LAC-53, LAC-66 | Database logging modules | Access attempts are stored in the database for later consultation and are separate from the user interfaces. |
| NFR-10 | LAC-55 | GUI and physical-mode lock control | The software prevents the graphical and physical access modes from operating simultaneously. |
| NFR-11 | LAC-47, LAC-51, LAC-55, LAC-67 | Local camera, facial recognition, database, and access modules | Main processing, facial identification, database queries, and access decisions run locally on the system. |

## Documentation and Diagrams

| Jira Key | Change | Evidence |
|---|---|---|
| LAC-57 | Update documentation and diagrams | DF0, DF1, system flow, general flow, process, sequence, and states diagrams were updated in English. |
| LAC-58 | Translate requirements and add facial requirements | `Requirements.md` was updated to English and extended through FR-23 and NFR-11. |
| LAC-74 | Create system architecture diagram | `documentacion/system_architecture.md` documents the interaction between hardware, software modules, database, facial recognition, and physical outputs. |
| LAC-79 | Rebuild traceability in English with Jira keys | This document replaces the previous issue-based traceability with the current Jira-based project traceability. |