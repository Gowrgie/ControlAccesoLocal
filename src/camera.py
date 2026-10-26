"""Camera module.

Opens the camera, captures frames and releases the device. It never raises
when the camera is missing or fails: open() returns False and last_error
explains why, so the button-based access keeps working.

Requirements: python3-opencv  (sudo apt install python3-opencv)
"""

import atexit
import threading
import time

try:
    import cv2
except ImportError:
    cv2 = None

DEFAULT_INDEX = 0
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 480
DEFAULT_FPS = 30
WARMUP_FRAMES = 5        # frames discarded while auto-exposure settles
MAX_READ_FAILURES = 5    # consecutive failed reads before the camera is dropped
MIN_BRIGHTNESS = 5.0     # mean pixel value below this means a covered lens


class Camera:
    """Single camera used to capture frames for face recognition."""

    def __init__(self, index=DEFAULT_INDEX, width=DEFAULT_WIDTH,
                 height=DEFAULT_HEIGHT, fps=DEFAULT_FPS):
        self.index = index
        self.width = width
        self.height = height
        self.fps = fps
        self.last_error = None
        self._capture = None
        self._failures = 0
        self._lock = threading.Lock()
        atexit.register(self.release)

    # ------------------------------------------------------------------ state
    @property
    def is_open(self):
        return self._capture is not None and self._capture.isOpened()

    def _set_error(self, message):
        self.last_error = message
        print(f"[camera] {message}")

    # ------------------------------------------------------------ open/release
    def open(self):
        """Open the camera. Returns True on success, False otherwise."""
        with self._lock:
            if self.is_open:
                return True
            if cv2 is None:
                self._set_error("OpenCV (cv2) is not installed")
                return False
            try:
                backend = getattr(cv2, "CAP_V4L2", cv2.CAP_ANY)
                capture = cv2.VideoCapture(self.index, backend)
                if not capture.isOpened():
                    capture.release()
                    self._set_error(f"camera {self.index} not found or busy")
                    return False

                capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                capture.set(cv2.CAP_PROP_FPS, self.fps)
                capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # always the latest frame

                for _ in range(WARMUP_FRAMES):
                    capture.read()
                ok, frame = capture.read()
                if not ok or frame is None or frame.size == 0:
                    capture.release()
                    self._set_error("camera opened but does not deliver frames")
                    return False

                self._capture = capture
                self._failures = 0
                self.last_error = None
                return True
            except Exception as error:
                self._set_error(f"could not open camera: {error}")
                self._release_locked()
                return False

    def _release_locked(self):
        if self._capture is not None:
            try:
                self._capture.release()
            except Exception:
                pass
            self._capture = None

    def release(self):
        """Free the camera device. Safe to call more than once."""
        with self._lock:
            self._release_locked()

    # ---------------------------------------------------------------- capture
    def read_frame(self):
        """Return one BGR frame (numpy array) or None if it could not be read."""
        with self._lock:
            if not self.is_open:
                return None
            try:
                ok, frame = self._capture.read()
            except Exception as error:
                ok, frame = False, None
                self._set_error(f"read error: {error}")

            if not ok or frame is None or frame.size == 0:
                self._failures += 1
                if self._failures >= MAX_READ_FAILURES:
                    self._set_error("camera stopped delivering frames")
                    self._release_locked()
                return None

            self._failures = 0
            return frame

    @staticmethod
    def is_usable(frame):
        """False for empty frames or a covered lens (almost black image)."""
        return frame is not None and frame.size > 0 and float(frame.mean()) > MIN_BRIGHTNESS

    def capture_frames(self, count=5, interval=0.2):
        """Capture up to `count` usable frames, `interval` seconds apart."""
        frames = []
        attempts = 0
        while len(frames) < count and attempts < count * 3 and self.is_open:
            attempts += 1
            frame = self.read_frame()
            if self.is_usable(frame):
                frames.append(frame)
                time.sleep(interval)
        return frames

    # --------------------------------------------------------- context manager
    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()
        return False

def camara_disponible():
    """Comprueba que la cámara pueda entregar un fotograma y la libera."""
    camara = Camera()

    try:
        if not camara.open():
            return False

        return camara.read_frame() is not None

    except Exception as error:
        print(f"[CAMARA] Error al comprobar disponibilidad: {error}", flush=True)
        return False

    finally:
        camara.release()


if __name__ == "__main__":
    # Quick hardware check:  python3 camera.py
    camera = Camera()
    if camera.open():
        captured = camera.capture_frames(3)
        shape = captured[0].shape if captured else "n/a"
        print(f"Captured {len(captured)} frame(s), size: {shape}")
        camera.release()
    else:
        print(f"Camera unavailable: {camera.last_error}")