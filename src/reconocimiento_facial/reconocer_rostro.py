"""Reconocimiento facial con la cámara y las incrustaciones activas de MySQL."""

import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

from camera import Camera
from scripts_db.db_conexion import cargar_embeddings_activos
from .calidad_captura import evaluar_calidad


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

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
PROCESAR_CADA = 3
ANCHO_PREVIEW = 800
ALTO_PREVIEW = 450
MAX_FALLOS_CAMARA = 10

COLOR_ESPERA = "#a66500"
COLOR_AUTORIZADO = "#188038"
COLOR_DENEGADO = "#b3261e"
COLOR_ERROR = "#5f6368"

COLOR_CV_ESPERA = (0, 165, 255)
COLOR_CV_AUTORIZADO = (0, 180, 0)
COLOR_CV_DENEGADO = (0, 0, 255)


# ---------------------------------------------------------------------------
# Carga de modelos y muestras faciales
# ---------------------------------------------------------------------------

def cargar_datos():
    """Carga YuNet, SFace y las muestras activas almacenadas en MySQL."""

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

    if not embeddings_por_usuario:
        raise ValueError(
            "No hay incrustaciones SFace válidas de usuarios activos en MySQL. "
            "Registra primero los rostros y guarda el modelo como 'sface'."
        )

    return detector, reconocedor, embeddings_por_usuario


# ---------------------------------------------------------------------------
# Ventana de reconocimiento
# ---------------------------------------------------------------------------

class VentanaReconocimiento:
    """Muestra la cámara y comunica el resultado al programa principal.

    `callback_resultado`, si se proporciona, recibe:
        callback_resultado(resultado, id_usuario)

    Los valores posibles de resultado son:
        autorizado, sin_permiso, no_reconocido, error_sistema
    """

    def __init__(
        self,
        parent,
        callback_identificacion=None,
        callback_cancelacion=None,
        callback_error=None,
    ):
        self.parent = parent
        self.callback_identificacion = callback_identificacion
        self.callback_cancelacion = callback_cancelacion
        self.callback_error = callback_error

        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Reconocimiento facial")
        self.ventana.protocol("WM_DELETE_WINDOW", self.cerrar)

        self.terminado = False
        self.resultado_final = False
        self.cancelacion_notificada = False
        self.after_id = None
        self.contador_cuadros = 0
        self.fallos_lectura = 0
        self.rostros_actuales = []
        self.imagen_tk = None
        self.camara = None

        self.detector = None
        self.reconocedor = None
        self.embeddings_por_usuario = {}

        self.color_cuadro = COLOR_CV_ESPERA
        self.resultado_pendiente = None
        self.id_usuario_pendiente = None

        self.configurar_ventana()
        self.crear_interfaz()

        try:
            (
                self.detector,
                self.reconocedor,
                self.embeddings_por_usuario,
            ) = cargar_datos()

            self.camara = Camera(index=0, width=640, height=480, fps=30)

            if not self.camara.open():
                detalle = self.camara.last_error or "No se pudo abrir la cámara."
                raise RuntimeError(detalle)

        except Exception as error:
            self.terminar(error=str(error))
            return

        self.after_id = self.ventana.after(30, self.actualizar_video)

    def configurar_ventana(self):
        ancho_pantalla = self.ventana.winfo_screenwidth()
        alto_pantalla = self.ventana.winfo_screenheight()

        ancho = min(920, ancho_pantalla - 30)
        alto = min(760, alto_pantalla - 40)
        x = max(0, (ancho_pantalla - ancho) // 2)
        y = max(0, (alto_pantalla - alto) // 2)

        self.ventana.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.ventana.minsize(700, 600)

    def crear_interfaz(self):
        contenedor = ttk.Frame(self.ventana, padding=14)
        contenedor.pack(fill="both", expand=True)

        ttk.Label(
            contenedor,
            text="Reconocimiento facial",
            font=("TkDefaultFont", 20, "bold"),
        ).pack(pady=(0, 10))

        self.panel_estado = tk.Frame(
            contenedor,
            bg=COLOR_ESPERA,
            padx=12,
            pady=9,
        )
        self.panel_estado.pack(fill="x", pady=(0, 10))

        self.estado_var = tk.StringVar(value="ESPERANDO ROSTRO")
        self.etiqueta_estado = tk.Label(
            self.panel_estado,
            textvariable=self.estado_var,
            bg=COLOR_ESPERA,
            fg="white",
            font=("TkDefaultFont", 20, "bold"),
        )
        self.etiqueta_estado.pack()

        self.detalle_var = tk.StringVar(
            value="Coloca una sola persona frente a la cámara."
        )
        self.etiqueta_detalle = tk.Label(
            self.panel_estado,
            textvariable=self.detalle_var,
            bg=COLOR_ESPERA,
            fg="white",
            font=("TkDefaultFont", 11),
            wraplength=850,
        )
        self.etiqueta_detalle.pack(pady=(3, 0))

        self.video_label = tk.Label(
            contenedor,
            text="Iniciando cámara…",
            bg="#171717",
            fg="white",
            anchor="center",
        )
        self.video_label.pack(fill="both", expand=True, pady=(0, 10))

        ttk.Button(
            contenedor,
            text="Cerrar",
            command=self.cerrar,
        ).pack(pady=(0, 2), ipadx=18, ipady=5)

    def mostrar_estado(self, titulo, detalle, tipo):
        colores = {
            "espera": (COLOR_ESPERA, COLOR_CV_ESPERA),
            "autorizado": (COLOR_AUTORIZADO, COLOR_CV_AUTORIZADO),
            "denegado": (COLOR_DENEGADO, COLOR_CV_DENEGADO),
            "error": (COLOR_ERROR, COLOR_CV_ESPERA),
        }

        fondo, color_cuadro = colores[tipo]
        self.estado_var.set(titulo)
        self.detalle_var.set(detalle)
        self.panel_estado.configure(bg=fondo)
        self.etiqueta_estado.configure(bg=fondo)
        self.etiqueta_detalle.configure(bg=fondo)
        self.color_cuadro = color_cuadro

    # -----------------------------------------------------------------------
    # Detección y comparación
    # -----------------------------------------------------------------------

    def procesar_imagen(self, imagen):
        alto, ancho = imagen.shape[:2]
        self.detector.setInputSize((ancho, alto))

        _, rostros = self.detector.detect(imagen)
        self.rostros_actuales = [] if rostros is None else list(rostros)

        problemas = evaluar_calidad(imagen, self.rostros_actuales)

        if problemas:
            if not self.rostros_actuales:
                titulo = "ESPERANDO ROSTRO"
            else:
                titulo = "VALIDACIÓN PENDIENTE"

            self.mostrar_estado(titulo, problemas[0], "espera")
            return

        rostro = self.rostros_actuales[0]

        try:
            cara_alineada = self.reconocedor.alignCrop(imagen, rostro)
            caracteristica = self.reconocedor.feature(cara_alineada)
            caracteristica = np.asarray(
                caracteristica,
                dtype=np.float32,
            ).reshape(1, -1)
        except (cv2.error, ValueError, TypeError) as error:
            print("[FACIAL] No se pudo procesar el rostro:", error, flush=True)
            self.mostrar_estado(
                "VALIDACIÓN PENDIENTE",
                "No se pudo procesar el rostro. Ajusta la posición e intenta.",
                "espera",
            )
            return

        mejor_id_usuario = None
        mejor_puntaje = -1.0

        for id_usuario, vectores in self.embeddings_por_usuario.items():
            for plantilla in vectores:
                if plantilla.shape != caracteristica.shape:
                    continue

                try:
                    puntaje = self.reconocedor.match(
                        caracteristica,
                        plantilla,
                        cv2.FaceRecognizerSF_FR_COSINE,
                    )
                    puntaje = float(puntaje)
                except (cv2.error, ValueError, TypeError):
                    continue

                if puntaje > mejor_puntaje:
                    mejor_puntaje = puntaje
                    mejor_id_usuario = id_usuario

        # El reconocedor de base de datos registra el intento facial y valida
        # que el usuario siga activo y tenga permiso de apertura.
        if mejor_id_usuario is not None and mejor_puntaje >= UMBRAL_SIMILITUD:
            self.terminar(id_usuario=mejor_id_usuario)
        else:
            self.terminar(id_usuario=None)

    def terminar(self, id_usuario=None, error=None):
        """Una sola salida por intento: id (o None) o un error."""
        if self.resultado_final:
            return
        self.resultado_final = True
        if self.camara is not None:
            self.camara.release()
            self.camara = None
        self.ventana.after_idle(self.entregar, id_usuario, error)

    def entregar(self, id_usuario, error):
        self.cerrar()  # libera la cámara y cierra la ventana
        if error is not None:
            if self.callback_error is not None:
                self.callback_error(error)
        elif self.callback_identificacion is not None:
            self.callback_identificacion(id_usuario)

    # -----------------------------------------------------------------------
    # Cámara y vista previa
    # -----------------------------------------------------------------------

    def actualizar_video(self):
        self.after_id = None

        if self.terminado or self.resultado_final:
            return
        if self.contador_cuadros > 600:  # ~20 s sin decisión: cancela el intento
            self.cerrar()
            return
        imagen = self.camara.read_frame() if self.camara is not None else None

        if imagen is None:
            self.fallos_lectura += 1

            if self.fallos_lectura >= MAX_FALLOS_CAMARA:
                self.terminar(error="La cámara dejó de enviar imágenes.")
                return

            self.after_id = self.ventana.after(100, self.actualizar_video)
            return

        self.fallos_lectura = 0
        self.contador_cuadros += 1

        if self.contador_cuadros % PROCESAR_CADA == 0:
            self.procesar_imagen(imagen)

        for rostro in self.rostros_actuales:
            x, y, ancho, alto = map(int, rostro[:4])
            cv2.rectangle(
                imagen,
                (x, y),
                (x + ancho, y + alto),
                self.color_cuadro,
                2,
            )

        alto, ancho = imagen.shape[:2]
        escala = min(ANCHO_PREVIEW / ancho, ALTO_PREVIEW / alto)
        dimensiones = (
            max(1, int(ancho * escala)),
            max(1, int(alto * escala)),
        )

        vista = cv2.resize(imagen, dimensiones)
        rgb = cv2.cvtColor(vista, cv2.COLOR_BGR2RGB)
        foto = ImageTk.PhotoImage(Image.fromarray(rgb))

        self.video_label.configure(image=foto, text="")
        self.imagen_tk = foto

        if not self.terminado and not self.resultado_final:
            self.after_id = self.ventana.after(15, self.actualizar_video)

    def cerrar(self):
        if self.terminado:
            return

        self.terminado = True

        if self.after_id is not None:
            try:
                self.ventana.after_cancel(self.after_id)
            except tk.TclError:
                pass
            self.after_id = None

        if self.camara is not None:
            self.camara.release()
            self.camara = None

        if (
            not self.resultado_final
            and self.callback_cancelacion is not None
            and not self.cancelacion_notificada
        ):
            self.cancelacion_notificada = True
            try:
                self.callback_cancelacion()
            except Exception as error:
                print("[FACIAL] Error al cancelar:", error, flush=True)

        try:
            self.ventana.destroy()
        except tk.TclError:
            pass


# ---------------------------------------------------------------------------
# Punto de entrada para que la interfaz principal pueda abrir esta ventana
# ---------------------------------------------------------------------------

def abrir_reconocimiento(
    parent,
    callback_identificacion=None,
    callback_cancelacion=None,
    callback_error=None,
):
    """Abre el reconocimiento como ventana secundaria de la aplicación."""
    return VentanaReconocimiento(
        parent,
        callback_identificacion=callback_identificacion,
        callback_cancelacion=callback_cancelacion,
        callback_error=callback_error,
    )