"""Ayuda a colocar correctamente el rostro antes de capturarlo o reconocerlo."""

# ---------------------------------------------------------------------------
# Importaciones
# ---------------------------------------------------------------------------

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Parámetros de calidad
# ---------------------------------------------------------------------------

# Brillo promedio mínimo aceptado en el recorte del rostro.
BRILLO_MINIMO = 65

# Tamaño del rostro respecto al cuadro completo de la cámara.
# Si es menor, se pide a la persona que se acerque.
ALTURA_ROSTRO_MINIMA = 0.22

# Si supera estos límites, se pide que se aleje y centre el rostro.
ALTURA_ROSTRO_MAXIMA = 0.82
ANCHO_ROSTRO_MAXIMO = 0.85

# Distancia mínima entre el rostro y los bordes del cuadro, en píxeles.
MARGEN_BORDE = 5


# ---------------------------------------------------------------------------
# Normalización de los resultados del detector
# ---------------------------------------------------------------------------

def _normalizar_rostros(rostros):
    """Convierte los resultados del detector en una lista de rostros.

    Acepta:
    - None, si no se detectó ningún rostro.
    - Un arreglo de NumPy, como el devuelto por FaceDetectorYN.detect.
    - Una sola fila que represente un rostro.
    - Una lista u otro iterable de rostros.
    """

    if rostros is None:
        return []

    if isinstance(rostros, np.ndarray):
        # Un arreglo vacío significa que no se detectaron rostros.
        if rostros.size == 0:
            return []

        # Un arreglo de una dimensión representa un solo rostro.
        if rostros.ndim == 1:
            return [rostros]

        # Si hay varias filas, cada una representa un rostro.
        return list(rostros)

    # Permite recibir listas u otros objetos iterables.
    return list(rostros)


# ---------------------------------------------------------------------------
# Evaluación de la imagen y generación de indicaciones
# ---------------------------------------------------------------------------

def evaluar_calidad(imagen, rostros):
    """Devuelve indicaciones para mejorar la captura.

    Comprueba que:
    - Se haya recibido una imagen.
    - Aparezca exactamente un rostro.
    - El rostro tenga un tamaño adecuado y esté dentro del cuadro.
    - Haya suficiente luz sobre el rostro.

    No evalúa nitidez ni rechaza imágenes por desenfoque o sobreexposición.

    Args:
        imagen: cuadro BGR recibido desde OpenCV.
        rostros: resultados de FaceDetectorYN.detect, un rostro individual,
                 una lista de rostros o None.

    Returns:
        Una lista de indicaciones. Una lista vacía significa que no encontró
        problemas de encuadre, distancia o iluminación.
    """

    # Comprobar que la cámara haya entregado una imagen válida.
    if imagen is None or not isinstance(imagen, np.ndarray) or imagen.size == 0:
        return ["No se recibió imagen de la cámara"]

    alto_imagen, ancho_imagen = imagen.shape[:2]

    # Normalizar los resultados para trabajar siempre con una lista.
    caras = _normalizar_rostros(rostros)

    # Solicitar que se coloque una persona frente a la cámara.
    if not caras:
        return ["No se detecta un rostro. Colócate frente a la cámara"]

    # Para una captura válida debe aparecer una sola persona.
    if len(caras) > 1:
        return ["Debe aparecer una sola persona frente a la cámara"]

    # La primera fila contiene los datos del rostro:
    # x, y, ancho, alto, puntos faciales y confianza.
    x, y, ancho_rostro, alto_rostro = map(int, caras[0][:4])

    # Limitar las coordenadas del rostro a los bordes de la imagen.
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(ancho_imagen, x + ancho_rostro)
    y2 = min(alto_imagen, y + alto_rostro)

    # Recortar la imagen para revisar únicamente la zona del rostro.
    recorte = imagen[y1:y2, x1:x2]

    if recorte.size == 0:
        return ["Centra el rostro dentro de la imagen"]

    indicaciones = []

    # Comparar el tamaño del rostro con las dimensiones del cuadro.
    proporcion_alto = alto_rostro / max(1, alto_imagen)
    proporcion_ancho = ancho_rostro / max(1, ancho_imagen)

    # Si el rostro ocupa muy poco espacio, la persona está lejos.
    if proporcion_alto < ALTURA_ROSTRO_MINIMA:
        indicaciones.append("Acércate un poco a la cámara")

    # Si el rostro es demasiado grande o toca los bordes,
    # pedir que la persona se aleje y centre.
    elif (
        proporcion_alto > ALTURA_ROSTRO_MAXIMA
        or proporcion_ancho > ANCHO_ROSTRO_MAXIMO
        or x1 <= MARGEN_BORDE
        or y1 <= MARGEN_BORDE
        or x2 >= ancho_imagen - MARGEN_BORDE
        or y2 >= alto_imagen - MARGEN_BORDE
    ):
        indicaciones.append("Aléjate un poco y centra el rostro")

    # Convertir el recorte a escala de grises para medir su brillo.
    gris = cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY)
    brillo_promedio = float(np.mean(gris))

    # Si el brillo promedio es bajo, recomendar más luz frontal.
    if brillo_promedio < BRILLO_MINIMO:
        indicaciones.append("Necesita más luz frontal para reconocer el rostro")

    return indicaciones