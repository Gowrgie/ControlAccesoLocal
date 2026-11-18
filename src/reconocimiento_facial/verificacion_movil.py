"""Verificación 1 a N de las capturas móviles de un reto facial."""

import os
from hashlib import sha256
from io import BytesIO
from math import atan2, degrees
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .calidad_captura import evaluar_calidad
from .comparacion import (
    cargar_modelos,
    cargar_muestras,
    detectar_rostros,
    extraer_embedding,
    identificar_embedding,
)

# MiniFASNetV2 2.7x, revisión publicada en la guía de configuración.
MODELO_PAD_SHA256 = "0cbe5caec95c31de9d2ef845cb85407d76aecd1b6a2c0e343f7d35306bfbccb8"
UMBRAL_PAD = 0.90
UMBRAL_IDENTIDAD = 0.45
MARGEN_IDENTIDAD = 0.05
LADO_MAXIMO = 1280
ROTACION_RESCATE = 30


def _decodificar(jpeg):
    try:
        with Image.open(BytesIO(jpeg), formats=("JPEG",)) as imagen:
            if max(imagen.size) > LADO_MAXIMO or min(imagen.size) < 160:
                return None
            rgb = np.asarray(imagen.convert("RGB"))
    except (OSError, ValueError, Image.DecompressionBombError):
        return None
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def _inclinacion(rostro):
    ojo_izquierdo, ojo_derecho = sorted((rostro[4:6], rostro[6:8]), key=lambda ojo: ojo[0])
    dx, dy = ojo_derecho - ojo_izquierdo
    return degrees(atan2(dy, dx))


class VerificadorFacialMovil:
    def __init__(self, modelo_pad):
        self._diagnostico = os.getenv("MOBILE_FACE_DIAGNOSTICS") == "1"
        ruta_pad = Path(modelo_pad)
        if sha256(ruta_pad.read_bytes()).hexdigest() != MODELO_PAD_SHA256:
            raise ValueError("El archivo MiniFASNetV2 no coincide con la revisión esperada")
        try:
            self._pad = cv2.dnn.readNetFromONNX(str(ruta_pad))
            self._detector, self._reconocedor = cargar_modelos()
        except cv2.error as error:
            raise RuntimeError("No se pudieron cargar los modelos faciales") from error

    def _rostro_vivo(self, imagen, rostro):
        alto, ancho = imagen.shape[:2]
        x, y, w, h = rostro[:4]
        escala = min(2.7, (ancho - 1) / w, (alto - 1) / h)
        w_recorte, h_recorte = int(w * escala), int(h * escala)
        x1 = int(np.clip(x + (w - w_recorte) / 2, 0, ancho - w_recorte - 1))
        y1 = int(np.clip(y + (h - h_recorte) / 2, 0, alto - h_recorte - 1))
        recorte = imagen[y1:y1 + h_recorte + 1, x1:x1 + w_recorte + 1]
        self._pad.setInput(cv2.dnn.blobFromImage(recorte, size=(80, 80)))
        logits = self._pad.forward().reshape(-1)
        if logits.size != 3 or not np.isfinite(logits).all():
            return False
        probabilidades = np.exp(logits - logits.max())
        return probabilidades[1] / probabilidades.sum() >= UMBRAL_PAD

    def _rechazar(self, motivo):
        if self._diagnostico:
            print(f"[FACIAL MÓVIL] {motivo}", flush=True)
        return None

    def _analizar(self, jpeg, captura, rotacion_rescate=0):
        imagen = _decodificar(jpeg)
        if imagen is None:
            return self._rechazar(f"{captura}: formato o tamaño de imagen inválido")
        rostros = detectar_rostros(self._detector, imagen)
        rotacion_aplicada = 0
        if not rostros and rotacion_rescate:
            alto, ancho = imagen.shape[:2]
            matriz = cv2.getRotationMatrix2D((ancho / 2, alto / 2), rotacion_rescate, 1)
            imagen = cv2.warpAffine(imagen, matriz, (ancho, alto))
            rostros = detectar_rostros(self._detector, imagen)
            rotacion_aplicada = rotacion_rescate

        indicaciones = evaluar_calidad(imagen, rostros)
        if indicaciones:
            return self._rechazar(f"{captura}: {indicaciones[0]}")
        rostro = rostros[0]
        if not self._rostro_vivo(imagen, rostro):
            return self._rechazar(f"{captura}: prueba de vida rechazada")
        # El reto se comprueba con el ángulo de la captura original.
        angulo = _inclinacion(rostro) + rotacion_aplicada
        return extraer_embedding(self._reconocedor, imagen, rostro), angulo

    def verificar(self, frontal, inclinada, direccion):
        """Identifica al usuario si ambas capturas pasan los controles."""
        try:
            return self._verificar(frontal, inclinada, direccion)
        except cv2.error as error:
            raise RuntimeError("Falló el procesamiento facial") from error

    def _verificar(self, frontal, inclinada, direccion):
        primero = self._analizar(frontal, "captura frontal")
        if primero is None:
            return None
        rotacion = ROTACION_RESCATE if direccion == "izquierda" else -ROTACION_RESCATE
        segundo = self._analizar(inclinada, "captura inclinada", rotacion)
        if segundo is None:
            return None

        vector_frontal, angulo_frontal = primero
        vector_inclinado, angulo_inclinado = segundo
        giro = angulo_inclinado - angulo_frontal
        giro_esperado = giro if direccion == "izquierda" else -giro
        if not abs(angulo_frontal) <= 10:
            return self._rechazar("captura frontal: cabeza fuera del ángulo inicial")
        if giro_esperado < 0:
            return self._rechazar("captura inclinada: dirección opuesta al reto")
        if not 15 <= giro_esperado <= 45:
            return self._rechazar("captura inclinada: ángulo insuficiente o excesivo")

        muestras = cargar_muestras()
        if not muestras:
            return self._rechazar("no hay muestras utilizables de usuarios activos")
        criterios = {"umbral": UMBRAL_IDENTIDAD, "margen": MARGEN_IDENTIDAD}
        id_usuario = identificar_embedding(self._reconocedor, vector_frontal, muestras, **criterios)
        if id_usuario is None:
            return self._rechazar("captura frontal: sin coincidencia facial clara")
        id_segundo = identificar_embedding(self._reconocedor, vector_inclinado, muestras, **criterios)
        if id_segundo != id_usuario:
            return self._rechazar("captura inclinada: sin coincidencia con la primera")
        return id_usuario
