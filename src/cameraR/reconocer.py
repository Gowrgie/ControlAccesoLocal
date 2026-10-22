import cv2
import json
import os
import numpy as np

CAMARA = "/dev/video0"
YUNET = "/home/jechairez/modelos/yunet.onnx"
SFACE = "/home/jechairez/modelos/sface.onnx"
ARCHIVO_PLANTILLAS = "/home/jechairez/modelos/plantillas.json"
MAX_MUESTRAS = 5
UMBRAL_INICIAL = 0.363

if not os.path.exists(YUNET):
    raise SystemExit(f"No encuentro el modelo YuNet: {YUNET}")

if not os.path.exists(SFACE):
    raise SystemExit(f"No encuentro el modelo SFace: {SFACE}")

modo = input("Escribe R para registrar o I para identificar: ").strip().lower()

if modo not in ("r", "i"):
    raise SystemExit("Opción no válida. Escribe R o I.")

plantillas = {}

if os.path.exists(ARCHIVO_PLANTILLAS):
    with open(ARCHIVO_PLANTILLAS, "r") as archivo:
        plantillas = json.load(archivo)

if modo == "r":
    nombre = input("Nombre o identificador de prueba: ").strip()
    if not nombre:
        raise SystemExit("Debes escribir un identificador.")

if modo == "i" and not plantillas:
    raise SystemExit("No hay rostros registrados. Primero ejecuta el modo R.")

detector = cv2.FaceDetectorYN.create(
    YUNET,
    "",
    (320, 320),
    0.8,
    0.3,
    5000,
)

reconocedor = cv2.FaceRecognizerSF.create(SFACE, "")

camara = cv2.VideoCapture(CAMARA, cv2.CAP_V4L2)
camara.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
camara.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not camara.isOpened():
    raise SystemExit("No se pudo abrir /dev/video0.")

muestras = []

if modo == "r":
    print("Mira a la cámara.")
    print("Con la ventana del video seleccionada, presiona r cinco veces.")
    print("Se guardará automáticamente al llegar a 5/5.")
else:
    print("Mira a la cámara para comparar tu rostro.")
    print("Presiona q en la ventana para salir.")

try:
    while True:
        ok, imagen = camara.read()

        if not ok:
            print("No se pudo leer la cámara.")
            break

        alto, ancho = imagen.shape[:2]
        detector.setInputSize((ancho, alto))
        _, rostros = detector.detect(imagen)

        rostro_actual = None
        caracteristica = None
        texto = "No se detecta rostro"

        if rostros is not None and len(rostros) > 0:
            # Si aparecen varias caras, usa la más grande.
            rostro_actual = max(rostros, key=lambda cara: cara[2] * cara[3])

            cara_alineada = reconocedor.alignCrop(imagen, rostro_actual)
            caracteristica = reconocedor.feature(cara_alineada)

            x, y, w, h = map(int, rostro_actual[:4])
            cv2.rectangle(
                imagen,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2,
            )

            if modo == "r":
                texto = f"Muestras: {len(muestras)}/{MAX_MUESTRAS} | Presiona r"

            else:
                mejor_nombre = "Desconocido"
                mejor_puntaje = -1.0

                for nombre_guardado, vectores in plantillas.items():
                    for vector in vectores:
                        plantilla = np.array(
                            vector,
                            dtype=np.float32,
                        ).reshape(1, -1)

                        puntaje = reconocedor.match(
                            caracteristica,
                            plantilla,
                            cv2.FaceRecognizerSF_FR_COSINE,
                        )

                        if puntaje > mejor_puntaje:
                            mejor_puntaje = puntaje
                            mejor_nombre = nombre_guardado

                if mejor_puntaje >= UMBRAL_INICIAL:
                    texto = f"{mejor_nombre} | similitud: {mejor_puntaje:.3f}"
                else:
                    texto = f"Desconocido | similitud: {mejor_puntaje:.3f}"

        cv2.putText(
            imagen,
            texto,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )

        cv2.imshow("Prueba de reconocimiento", imagen)
        tecla = cv2.waitKey(1) & 0xFF

        if modo == "r" and tecla == ord("r"):
            if caracteristica is None:
                print("No se detecta una cara. Mira a la cámara e intenta otra vez.")
            elif len(muestras) < MAX_MUESTRAS:
                muestras.append(caracteristica.flatten().tolist())
                print(f"Muestra registrada: {len(muestras)}/{MAX_MUESTRAS}")

                if len(muestras) == MAX_MUESTRAS:
                    plantillas[nombre] = muestras

                    with open(ARCHIVO_PLANTILLAS, "w") as archivo:
                        json.dump(plantillas, archivo)

                    print(f"Registro de {nombre} guardado.")
                    break

        if tecla == ord("q"):
            break

finally:
    camara.release()
    cv2.destroyAllWindows()