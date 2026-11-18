"""Carga y comparación facial compartidas por los flujos de acceso."""

import os
from pathlib import Path

import cv2
import numpy as np

from scripts_db.db_conexion import cargar_embeddings_activos


# Por defecto busca los modelos en ~/modelos.
# Se puede cambiar la carpeta con la variable MODELOS_FACIALES_DIR.
DIRECTORIO_MODELOS = Path(
    os.environ.get(
        "MODELOS_FACIALES_DIR",
        str(Path.home() / "modelos"),
    )
)

YUNET = Path(
    os.environ.get(
        "YUNET_MODEL_PATH",
        str(DIRECTORIO_MODELOS / "yunet.onnx"),
    )
)
SFACE = Path(
    os.environ.get(
        "SFACE_MODEL_PATH",
        str(DIRECTORIO_MODELOS / "sface.onnx"),
    )
)

# Este valor debe ser igual al que registrar_rostro.py escriba en la columna
# "modelo" de la tabla embeddings_faciales.
MODELO_EMBEDDING = "sface"

UMBRAL_SIMILITUD = 0.363


def cargar_datos():
    """Carga YuNet, SFace y las muestras activas almacenadas en MySQL."""

    detector, reconocedor = cargar_modelos()
    muestras = cargar_muestras()
    if not muestras:
        raise ValueError(
            "No hay incrustaciones SFace válidas de usuarios activos en MySQL. "
            "Registra primero los rostros y guarda el modelo como 'sface'."
        )
    return detector, reconocedor, muestras


def cargar_modelos():
    for ruta in (YUNET, SFACE):
        if not ruta.is_file():
            raise FileNotFoundError(f"No encuentro el modelo: {ruta}")

    detector = cv2.FaceDetectorYN.create(
        str(YUNET),
        "",
        (320, 320),
        0.8,
        0.3,
        5000,
    )
    reconocedor = cv2.FaceRecognizerSF.create(str(SFACE), "")

    return detector, reconocedor


def cargar_muestras():
    # La vista devuelve solamente embeddings de usuarios activos.
    filas = cargar_embeddings_activos()
    embeddings_por_usuario = {}

    for fila in filas:
        modelo = str(fila.get("modelo") or "").strip().casefold()

        # No comparar vectores generados por modelos distintos.
        if modelo != MODELO_EMBEDDING:
            continue

        id_usuario = fila.get("id_usuario")
        datos_embedding = fila.get("embedding")

        if id_usuario is None or datos_embedding is None:
            continue

        try:
            vector = np.frombuffer(bytes(datos_embedding), dtype=np.float32)
        except (TypeError, ValueError):
            continue

        # SFace genera un vector de 128 valores float32.
        if vector.size != 128:
            continue

        embeddings_por_usuario.setdefault(int(id_usuario), []).append(
            vector.reshape(1, -1)
        )

    return embeddings_por_usuario


def detectar_rostros(detector, imagen):
    """Devuelve los rostros detectados por YuNet en una imagen BGR."""
    alto, ancho = imagen.shape[:2]
    detector.setInputSize((ancho, alto))
    _, rostros = detector.detect(imagen)
    return [] if rostros is None else list(rostros)


def extraer_embedding(reconocedor, imagen, rostro):
    """Alinea el rostro y devuelve el vector SFace normalizado a una fila."""
    cara_alineada = reconocedor.alignCrop(imagen, rostro)
    caracteristica = reconocedor.feature(cara_alineada)
    return np.asarray(caracteristica, dtype=np.float32).reshape(1, -1)


def identificar_embedding(
    reconocedor, caracteristica, embeddings_por_usuario, *, umbral=UMBRAL_SIMILITUD, margen=0.0
):
    """Devuelve el usuario de la mejor coincidencia o None."""
    mejor_id_usuario = None
    mejor_puntaje = segundo_puntaje = -1.0

    for id_usuario, vectores in embeddings_por_usuario.items():
        puntaje_usuario = -1.0
        for plantilla in vectores:
            if plantilla.shape != caracteristica.shape:
                continue

            try:
                puntaje = float(reconocedor.match(
                    caracteristica, plantilla, cv2.FaceRecognizerSF_FR_COSINE
                ))
            except (cv2.error, ValueError, TypeError):
                continue

            if puntaje > puntaje_usuario:
                puntaje_usuario = puntaje

        if puntaje_usuario > mejor_puntaje:
            segundo_puntaje = mejor_puntaje
            mejor_puntaje = puntaje_usuario
            mejor_id_usuario = id_usuario
        elif puntaje_usuario > segundo_puntaje:
            segundo_puntaje = puntaje_usuario

    if mejor_puntaje >= umbral and mejor_puntaje - segundo_puntaje >= margen:
        return mejor_id_usuario
    return None
