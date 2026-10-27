import os
import sys
import time

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
DETECTOR_PATH = os.path.join(MODEL_DIR, "face_detection_yunet_2023mar.onnx")
RECOGNIZER_PATH = os.path.join(MODEL_DIR, "face_recognition_sface_2021dec.onnx")

MODEL_NAME = "sface_2021dec"   # goes to the "modelo" column of embeddings_faciales
MIN_FACE_SIZE = 80             # pixels; smaller faces are too far and are ignored
SAME_PERSON_THRESHOLD = 0.363  # cosine similarity recommended for SFace

_detector = None
_recognizer = None


def load_models():
    """Load both models. Returns True on success, False otherwise."""
    global _detector, _recognizer
    if _detector is not None:
        return True
    if cv2 is None:
        print("[face_engine] OpenCV or numpy is not installed")
        return False
    for path in (DETECTOR_PATH, RECOGNIZER_PATH):
        if not os.path.isfile(path):
            print(f"[face_engine] model file not found: {path}")
            return False
    try:
        _detector = cv2.FaceDetectorYN.create(DETECTOR_PATH, "", (320, 320), 0.8, 0.3, 50)
        _recognizer = cv2.FaceRecognizerSF.create(RECOGNIZER_PATH, "")
        return True
    except Exception as error:
        print(f"[face_engine] could not load models (OpenCV >= 4.8 needed): {error}")
        _detector = None
        return False


def get_embedding(frame):
    """Return (status, embedding) for one camera frame.

    status: "ok"              -> exactly one face, embedding is a numpy vector
            "no_face"         -> no face found (or too far away)
            "multiple_faces"  -> more than one face in the frame
            "error"           -> models or frame problem
    The embedding is None unless status is "ok".
    """
    if not load_models():
        return "error", None
    try:
        height, width = frame.shape[:2]
        _detector.setInputSize((width, height))
        _, faces = _detector.detect(frame)
        faces = [] if faces is None else [f for f in faces if min(f[2], f[3]) >= MIN_FACE_SIZE]

        if not faces:
            return "no_face", None
        if len(faces) > 1:
            return "multiple_faces", None

        aligned = _recognizer.alignCrop(frame, faces[0])
        embedding = _recognizer.feature(aligned).flatten().astype(np.float32)
        return "ok", embedding
    except Exception as error:
        print(f"[face_engine] error: {error}")
        return "error", None


def embedding_to_bytes(embedding):
    """Raw float32 bytes, the format of embeddings_faciales.embedding (BLOB)."""
    return np.asarray(embedding, dtype=np.float32).tobytes()


def embedding_from_bytes(data):
    return np.frombuffer(data, dtype=np.float32).copy()


def similarity(first, second):
    """Cosine similarity between two embeddings (higher = more alike)."""
    return float(np.dot(first, second) / (np.linalg.norm(first) * np.linalg.norm(second)))


if __name__ == "__main__":
    embeddings = []

    if len(sys.argv) > 1:                       # test with an image file
        image = cv2.imread(sys.argv[1])
        status, embedding = get_embedding(image)
        print(f"status: {status}")
        if status == "ok":
            embeddings.append(embedding)
    else:                                       # test with the camera
        from camera import Camera
        camera = Camera()
        if not camera.open():
            print(f"Camera unavailable: {camera.last_error}")
            sys.exit(1)
        for number in range(1, 4):
            print(f"\nLook at the camera... ({number}/3)")
            time.sleep(2)
            status, embedding = get_embedding(camera.read_frame())
            print(f"status: {status}")
            if status == "ok":
                embeddings.append(embedding)
        camera.release()

    for number, embedding in enumerate(embeddings, start=1):
        print(f"embedding {number}: size={embedding.size}, "
              f"first 5 values={[round(float(v), 4) for v in embedding[:5]]}")

    if embeddings:
        data = embedding_to_bytes(embeddings[0])
        print(f"BLOB: {len(data)} bytes, roundtrip "
              f"{'OK' if (embedding_from_bytes(data) == embeddings[0]).all() else 'FAILED'}")
    if len(embeddings) >= 2:
        value = similarity(embeddings[0], embeddings[1])
        verdict = "same person" if value >= SAME_PERSON_THRESHOLD else "different person"
        print(f"similarity capture 1 vs 2: {value:.3f} -> {verdict}")