# System Requirements

## Functional Requirements

**FR-01.** The system shall capture the input sequence, compare it against the information stored in the database, and determine whether access is authorized or denied.

**FR-02.** The system shall capture a user identifier and a passcode of 4 to 6 inputs.

**FR-03.** The system shall indicate via LED lights whether the passcode is valid (green) or invalid (red).

**FR-04.** The system shall reset after each capture to allow for new data entry.

**FR-05.** If more than 4 seconds elapse without a new input during an incomplete capture, the system shall clear the input buffer, discard the entered data, and automatically return to the home screen (standby state).

**FR-06.** The system shall emit a sound each time it returns to the standby state and is ready for a new capture.

**FR-07.** The system shall emit three short buzzer tones when evaluating the entered sequence, whether access is authorized or denied, coinciding with the activation of the corresponding green or red LED. In the event of a system failure, it shall emit one long tone.

**FR-08.** The system shall detect human presence using a PIR sensor and, while in standby, initiate or enable interaction by displaying the identification screen. PIR detection alone shall not authorize access.

**FR-09.** The system shall feature a simple graphical user interface (GUI) developed in Python, allowing the user to identify themselves, enter their passcode, and view the validation result.

**FR-10.** The system shall display the graphical interface on a monitor connected to the Raspberry Pi.

**FR-11.** The system shall store and query necessary information in a MySQL database, and log each access attempt with the date and time, user, mechanism used (GUI or physical buttons), and result.

**FR-12.** The system shall identify each user within the system and assign them one of three roles (administrator, technical service, or general user) with distinct permissions.

**FR-13.** The system shall validate access using the information stored in the database (user, passcode, role, and permissions) and distinguish between an authorized user, an authorized user without permission, incorrect information or unrecognized user, and a database query failure. The latter must not be treated as a standard denial.

**FR-14.** The system shall retain the physical button interface from the first version for passcode entry and use the same validation logic as the graphical interface, without duplication.

**FR-15.** When the graphical interface or monitor is unavailable, the system shall allow authentication, result display, and attempt logging to be completed using the physical buttons.

**FR-16.** When access is authorized, the system shall play the audio message "Access granted" ("Acceso correcto") through a speaker.

**FR-17.** When access is authorized, the system shall activate a motor representing the opening of the access point and return it to its resting position after 3 seconds. It shall not activate for any other result.

**FR-18.** The system shall return to a standby state after completing each operation, regardless of the result or the interface used, remaining ready to detect a new presence.

**FR-19:** The system shall support the guided enrollment of a new user via live facial capture and provide confirmation of successful registration.

**FR-20:** The system shall perform facial detection and identification completely locally, without relying on external cloud recognition services.

**FR-21:** The system shall unequivocally associate the biometric representation with a local user record and their permissions.

**FR-22:** After identifying a user's face, the system shall consult their permissions, authorize or reject access, and trigger the corresponding physical output.

**FR-23:** The system shall correctly reject access when an unregistered or unknown face is detected.

## Non-Functional Requirements

**NFR-01.** The system shall prevent registering false physical inputs due to button bounce (debounce) during both identifier and passcode capture.

**NFR-02.** Access information (user, passcode, role, and permissions) stored in the database shall be kept secure during system execution and may only be modified by the administrator.

**NFR-03.** The system shall evaluate and present the response (authorized/denied/failure) within no more than 1 second after capturing the final data point of the sequence, whether via the graphical interface or buttons.

**NFR-04.** The PIR sensor shall detect human presence and enable interaction within no more than 1 second.

**NFR-05.** The graphical interface shall be simple and intuitive, ensuring a user can identify themselves and complete validation without prior training.

**NFR-06.** The MySQL database query shall resolve within no more than 2 seconds; if this time is exceeded, the system shall treat it as a query failure.

**NFR-07.** The system shall allow operation via physical buttons without requiring a manual restart if the graphical interface or monitor becomes unavailable.

**NFR-08.** The "Access granted" audio message shall be played at a volume audible from a minimum distance of 1 meter from the access point.

**NFR-09.** Access attempt logs stored in the database shall not be lost or alterable from the graphical or button interfaces, and must remain available for future reference.

**NFR-10.** The system shall process one access operation at a time, preventing simultaneous validation of a graphical interface interaction and a button interaction on the same opening mechanism.

**NFR-11:** The main processing, database queries, and access decision logic must function entirely locally, even if a pre-trained model is used for the face recognition.
