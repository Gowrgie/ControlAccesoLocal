# Local Access Control

Local access control system for a Raspberry Pi. Users identify themselves with their face, a graphical interface, or three physical buttons. Access is checked against a local MySQL database and the result is shown with LEDs, a buzzer, a speaker and a servo that represents the access point.

## Objectives

- Allow local access without internet, using physical buttons, a graphical interface or facial recognition.
- Keep the buttons working as a fallback when the screen or the camera is not available.
- Record every access attempt with its date, user, method and result.

## Features

- **Three authentication methods:** physical buttons (3 buttons), graphical interface (Tkinter) and local facial recognition (camera).
- **Roles:** administrator, technical service and general user, with different permissions.
- **Presence detection:** a PIR sensor enables the interaction. The sensor alone never grants access.
- **Feedback:** green and red LEDs, a buzzer, speaker audio and the on-screen result.
- **Access point:** a servo opens for 3 seconds when access is authorized.
- **Access log:** every attempt is stored with date and time, user, method (`interfaz_grafica`, `botones` or `facial`) and result (`autorizado`, `sin_permiso`, `no_reconocido` or `error_sistema`).
- **Fallback:** if the screen is unavailable, the system runs with the physical buttons only (`--solo-botones`).

## Hardware

| Component | Purpose | Details |
|---|---|---|
| Raspberry Pi | Main controller | Runs the program and the database |
| 3 push buttons | Identifier and passcode entry | GPIO 14, 15 and 18 |
| PIR motion sensor | Presence detection | GPIO 27 |
| Green and red LEDs | Access result | GPIO 23 and 24 |
| Buzzer | Short audio signals | GPIO 25 |
| Servo | Access point | GPIO 26 |
| Camera | Facial recognition | [CONFIRM: USB camera, device /dev/video0] |
| Speaker | Audio feedback | [CONFIRM: connected to the 3.5 mm audio output] |
| Monitor | Graphical interface | Connected to the Raspberry Pi |

See `documentacion/hardware.md` for the full wiring and assembly guide.

## Software

| Module | Description |
|---|---|
| `src/hardware.py` | GPIO control: buttons, PIR, LEDs, buzzer and servo |
| `src/audio.py` | Speaker audio feedback |
| `src/camera.py` | Camera capture |
| `src/access_logic.py` | Access validation by role and by buttons |
| `src/access_flow.py` | Shared capture flow for buttons and graphical interface |
| `src/gui.py` | Graphical interface (Tkinter) |
| `src/headless_mode.py` | Button-only mode without a screen |
| `src/reconocimiento_facial/` | Face enrollment and face recognition |
| `src/scripts_db/` | Database connection and SQL scripts |

## Requirements

- Raspberry Pi with a Linux system, Python 3 and a MySQL server
- Python packages: `RPi.GPIO`, `lgpio`, `mysql-connector-python`, `opencv-python-headless` (4.8 or newer), `numpy`, `Pillow` and Tkinter
- System tools for audio: `speaker-test` (ALSA utilities) and `killall`
- Face models (not included in the repository), saved in `~/modelos/`:
  - `yunet.onnx` (face detection)
  - `sface.onnx` (face recognition)

```bash
mkdir -p ~/modelos && cd ~/modelos
wget -L -O yunet.onnx https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
wget -L -O sface.onnx https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx
```

## Database setup

Run these scripts from `src/scripts_db/` with an administrator MySQL account, in this order:

1. `db_squema.sql`: base schema (roles, users, access attempts)
2. `add_biometric_table.sql`: facial embeddings table
3. `add_user_active_flag.sql`: active flag for users
4. `grant_delete_embeddings.sql`: permission for the application user to delete embeddings

## How to run

```bash
cd src
[CONFIRM: command that starts the system]
python3 [CONFIRM: entry point] --solo-botones    # buttons only, no screen
```

To enroll a face for an existing user:

```bash
cd src
python3 -m reconocimiento_facial.registrar_rostro --id-usuario <user id>
```

## Team

- Sergio Becerril Tovar
- Gustavo **Nath**anael Calderon Castro
- Josue Delgado Nieto
- Jorge Herrera Uribe
- Axel Mendez Barrera
- Xavier Alexandro Padilla Arellano
- Diego Armando Rodriguez Martinez

## System status

In development.