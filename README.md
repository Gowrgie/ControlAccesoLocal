# Local Access Control

Local access control system for a Raspberry Pi. Users can use the Android app, the local graphical interface, three physical buttons, or the Raspberry Pi camera. Access is checked against a local MySQL database and the result is shown with LEDs, a buzzer, a speaker and a servo that represents the access point.

## Objectives

- Allow access over the local network from Android, or directly through the physical buttons, graphical interface, or Raspberry Pi camera.
- Keep the buttons working as a fallback when the screen or the camera is not available.
- Record every access attempt with its date, user, method and result.

## Features

- **Access methods:** physical buttons, the Tkinter interface, local facial recognition, and the Android app. The app offers ID and passcode sign-in and an optional Android biometric sign-in for linked phones.
- **Roles:** administrator, technical service and general user, with different permissions.
- **Presence detection:** a PIR sensor enables the interaction. The sensor alone never grants access.
- **Feedback:** green and red LEDs, a buzzer, speaker audio and the on-screen result.
- **Access point:** a servo opens for 3 seconds when access is authorized.
- **Access log:** every attempt is stored with date and time, user, method (`interfaz_grafica`, `botones`, `facial`, or `app_movil`) and result (`autorizado`, `sin_permiso`, `no_reconocido` or `error_sistema`).
- **Fallback:** use `--solo-botones` to run without the graphical interface. The mobile API can run in either mode.

## Hardware

| Component | Purpose | Details |
|---|---|---|
| Raspberry Pi | Main controller | Runs the program and the database |
| 3 push buttons | Identifier and passcode entry | GPIO 14, 15 and 18 |
| PIR motion sensor | Presence detection | GPIO 27 |
| Green and red LEDs | Access result | GPIO 23 and 24 |
| Buzzer | Short audio signals | GPIO 25 |
| Servo | Access point | GPIO 26 |
| Camera | Facial recognition | USB camera |
| Speaker | Audio feedback | Bluetooth |
| Monitor | Graphical interface | Connected to the Raspberry Pi |

See the [hardware documentation](documentacion/documentacion.md) for wiring and assembly details.

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
| `src/api/` | Local HTTPS API for mobile authentication, presence, and access requests |
| `app_movil/` | Android application |

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

Follow the [installation and migration procedure](documentacion/installation.md)
for a new or existing database. The mobile biometric credential migration uses
the existing MySQL database.

## How to run

From the repository root:

```bash
python3 src/Main_code.py
python3 src/Main_code.py --solo-botones
```

For the mobile app, configure HTTPS using the
[mobile API guide](documentacion/mobile_api_contract.md) and see the
[Android setup](app_movil/README.md).

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
