# Raspberry Pi 5 USB Camera and Face Recognition

## Overview

A USB webcam is connected to a Raspberry Pi 5 running Ubuntu. The camera was detected and tested locally with Python and OpenCV. The project is being prepared to detect and recognize faces locally using YuNet and SFace.

## Hardware and Camera

The webcam appears as **GC21 Video**. Ubuntu exposes these camera devices:

| Device | Details |
|---|---|
| `/dev/video0` | Video capture device used by the Python program |
| `/dev/video1` | Listed by the system, but could not be opened for capture |

Supported webcam formats:

- **MJPEG:** 1920×1080 or 1280×720, up to 60 fps
- **YUYV:** 640×360, 30 fps

The Python camera test successfully received a **1280×720** frame from `/dev/video0`.

## Software and Permissions

The following packages were installed:

```bash
sudo apt install guvcview python3-opencv python3-numpy
```

The camera initially returned a permission error. The user was added to the `video` group:

```bash
sudo usermod -aG video "$USER"
```

This change takes effect after logging out and back in, or restarting Ubuntu.

## Camera Capture Settings

The Python programs use OpenCV's V4L2 capture backend and request MJPEG at 1280×720:

```python
camara = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)
camara.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
camara.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
```

The camera test confirmed that `/dev/video0` returns image frames. `/dev/video1` did not open for capture, so the project uses `/dev/video0`.

## Face Detection and Recognition Models

The planned local models are:

- **YuNet:** detects faces in camera frames.
- **SFace:** generates facial feature vectors and compares them with enrolled templates.

The models are expected at:

```text
/home/jechairez/modelos/yunet.onnx
/home/jechairez/modelos/sface.onnx
```

The detection program uses YuNet with the live camera. Face detection was confirmed to draw a box around the detected face.

## Recognition Workflow

The provided `reconocer.py` program has two modes:

### Registration (`R`)

Enter a test identifier, then press `r` five times while a face is visible. The program saves the five SFace feature vectors to:

```text
/home/jechairez/modelos/plantillas.json
```

### Identification (`I`)

The program compares a detected face against saved templates and displays the best matching identifier and cosine similarity score. If the score is below the configured initial threshold (`0.363`), it displays **Desconocido**.

Run the program with:

```bash
python3 ~/reconocer.py
```

The registration and identification program has been provided, but successful enrollment and matching have not yet been confirmed.

## Current Scope and Limitations

- Camera capture and YuNet face detection have been confirmed.
- The SFace enrollment and identification flow is prepared for local testing.
- The similarity threshold is an initial reference value and has not been calibrated for this camera or environment.
- The current prototype does not perform liveness detection, connect to MySQL, or control a door or relay.