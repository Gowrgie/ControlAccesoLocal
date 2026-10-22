# Local Face Recognition with OpenCV, YuNet, and SFace

This guide explains how to run a Python face-recognition prototype with a USB webcam on Ubuntu or Windows.

The program has two modes:

- **Register (`R`)**: capture five face samples and save them as a local template.
- **Identify (`I`)**: compare the camera image with saved templates and display the closest match.

Face detection and comparison run locally. The program uses OpenCV's YuNet and SFace models. OpenCV documents these APIs for face detection and recognition; the SFace cosine threshold used below is only an initial reference and must be evaluated with the actual camera and lighting. [OpenCV face detection and recognition](https://docs.opencv.org/4.12.0/d0/dd4/tutorial_dnn_face.html)

## Requirements

- A computer running Ubuntu or Windows
- Python 3
- A working webcam
- The two ONNX model files:
  - `yunet.onnx`
  - `sface.onnx`
- The Python program saved as `reconocer.py`

The program also creates `plantillas.json` after a successful registration.

## 1. Install dependencies

### Ubuntu

Open a terminal and run:

```bash
sudo apt update
sudo apt install python3-opencv python3-numpy wget
```

OpenCV must provide the `FaceDetectorYN` and `FaceRecognizerSF` APIs. You can check them with:

```bash
python3 -c "import cv2, numpy; print('OpenCV:', cv2.__version__); print('YuNet:', hasattr(cv2, 'FaceDetectorYN')); print('SFace:', hasattr(cv2, 'FaceRecognizerSF'))"
```

The final two lines should show `True`.

### Windows

Install 64-bit Python 3, then open PowerShell in the project folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install opencv-contrib-python numpy
```

The OpenCV Python wheels are available through PyPI. Install only one OpenCV wheel variant in this environment; do not install both `opencv-python` and `opencv-contrib-python`. [OpenCV Python installation guide](https://docs.opencv.org/5.0/py_tutorials/py_setup/py_pip_install/py_pip_install.html) · [opencv-contrib-python on PyPI](https://pypi.org/project/opencv-contrib-python/)

Check that the APIs are available:

```powershell
py -c "import cv2, numpy; print('OpenCV:', cv2.__version__); print('YuNet:', hasattr(cv2, 'FaceDetectorYN')); print('SFace:', hasattr(cv2, 'FaceRecognizerSF'))"
```

The final two lines should show `True`.

## 2. Download the models

Create a folder named `modelos` in your home directory and download the model files from OpenCV Zoo.

### Ubuntu

```bash
mkdir -p ~/modelos
wget -O ~/modelos/yunet.onnx https://github.com/opencv/opencv_zoo/raw/refs/heads/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
wget -O ~/modelos/sface.onnx https://github.com/opencv/opencv_zoo/raw/refs/heads/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx
```

Check the files:

```bash
ls -lh ~/modelos
```

### Windows

In PowerShell, replace `YOUR_USER` with the Windows account name:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\modelos"
curl.exe -L "https://github.com/opencv/opencv_zoo/raw/refs/heads/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx" -o "$env:USERPROFILE\modelos\yunet.onnx"
curl.exe -L "https://github.com/opencv/opencv_zoo/raw/refs/heads/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx" -o "$env:USERPROFILE\modelos\sface.onnx"
```

The models are published in the OpenCV Zoo: [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) and [SFace](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface).

## 3. Configure the program for your operating system

The sample program contains fixed Ubuntu paths and the Linux V4L2 camera backend. Adjust its configuration before running it on Windows.

### Ubuntu configuration

Use these settings if the Ubuntu username is `jechairez` and the models are in `/home/jechairez/modelos`:

```python
CAMARA = "/dev/video0"
YUNET = "/home/jechairez/modelos/yunet.onnx"
SFACE = "/home/jechairez/modelos/sface.onnx"
ARCHIVO_PLANTILLAS = "/home/jechairez/modelos/plantillas.json"
```

Open the webcam with the V4L2 backend:

```python
camara = cv2.VideoCapture(CAMARA, cv2.CAP_V4L2)
```

If the Ubuntu username differs, update the `/home/jechairez/` paths accordingly.

### Windows configuration

Replace the paths with the Windows account's home folder. For example, if the account name is `Alex`:

```python
CAMARA = 0
YUNET = r"C:\Users\Alex\modelos\yunet.onnx"
SFACE = r"C:\Users\Alex\modelos\sface.onnx"
ARCHIVO_PLANTILLAS = r"C:\Users\Alex\modelos\plantillas.json"
```

Replace the camera initialization line:

```python
camara = cv2.VideoCapture(CAMARA, cv2.CAP_DSHOW)
```

The camera index `0` is the default webcam. If it does not open, try `1`. OpenCV provides the `CAP_DSHOW` backend for Windows DirectShow video capture. [OpenCV video I/O flags](https://docs.opencv.org/3.4.4/d4/d15/group__videoio__flags__base.html)

## 4. Save the Python program

Save the complete Python code as:

- Ubuntu: `~/reconocer.py`
- Windows: `C:\Users\YOUR_USER\reconocer.py`

The code should contain the operating-system-specific settings from the previous section.

## 5. Run the program

### Ubuntu

```bash
python3 ~/reconocer.py
```

### Windows

Activate the virtual environment from the project folder, if it is not already active, then run:

```powershell
.\.venv\Scripts\Activate.ps1
py .\reconocer.py
```

## 6. Register a face

1. At the prompt, type `R` and press Enter.
2. Enter a test name or ID, such as `test01`.
3. Look at the camera.
4. Select the video window and press the `r` key five times.
5. The program saves the registration automatically after sample `5/5`.

The templates are stored in `plantillas.json` inside the `modelos` folder. Keep this file protected because it contains biometric templates.

## 7. Identify a registered face

Run the program again and type `I` at the prompt. Look at the camera. The window displays the closest registered ID and its similarity score, or `Desconocido` if the score is below the configured threshold.

Press `q` while the video window is selected to quit.

## Troubleshooting

### Camera does not open

- Close other applications that may be using the webcam.
- On Windows, try camera index `1` instead of `0`.
- On Ubuntu, check that the camera is listed with `v4l2-ctl --list-devices` and that the user has permission to access `/dev/video0`.

### Model file not found

Confirm that the model paths in `reconocer.py` match the files' actual locations and filenames.

### No face is detected

Face the camera, improve the lighting, and move closer so the face is clearly visible.

### Recognition result is incorrect

The configured cosine threshold (`0.363`) is a starting reference, not a validated setting for a particular camera or environment. Test with the intended users, camera, lighting, and distance before relying on the result.

## Scope

This is a local recognition prototype. It displays a match result; it does not connect to MySQL or operate a door or relay. It does not include liveness detection. Obtain permission before registering anyone's face and protect or delete biometric templates when they are no longer needed.