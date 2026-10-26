"""Registro facial guiado para un usuario existente del sistema."""

import argparse
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

from camera import Camera
from scripts_db.database import (
    eliminar_embedding,
    insertar_embedding,
    leer_embeddings_usuario,
)
from scripts_db.db_conexion import obtener_permisos_por_usuario
from .calidad_captura import evaluar_calidad


# Puedes cambiar la carpeta mediante la variable MODELOS_FACIALES_DIR.
CARPETA_MODELOS = Path(
    os.environ.get("MODELOS_FACIALES_DIR", Path.home() / "modelos")
)
YUNET = Path(os.environ.get("YUNET_MODEL_PATH", CARPETA_MODELOS / "yunet.onnx"))
SFACE = Path(os.environ.get("SFACE_MODEL_PATH", CARPETA_MODELOS / "sface.onnx"))

MODELO_EMBEDDING = "sface"
MAX_MUESTRAS = 5
PROCESAR_CADA = 3
ANCHO_PREVIEW = 640
ALTO_PREVIEW = 360
MAX_FALLOS_CAMARA = 10
CUADROS_POSE_ESTABLE = 5
VENTANA_GIRO = 7
UMBRAL_POSE_FRONTAL = 0.10
UMBRAL_POSE_LATERAL = 0.14

SECUENCIA_POSES = ["frente", "izquierda", "frente", "derecha", "frente"]


def calcular_indice_giro(rostro):
    """Calcula un indicador de giro horizontal usando ojos y nariz de YuNet."""
    ojo_a = np.array([float(rostro[4]), float(rostro[5])])
    ojo_b = np.array([float(rostro[6]), float(rostro[7])])
    nariz = np.array([float(rostro[8]), float(rostro[9])])

    ojo_izquierdo, ojo_derecho = sorted((ojo_a, ojo_b), key=lambda punto: punto[0])
    distancia_ojos = float(np.linalg.norm(ojo_derecho - ojo_izquierdo))

    if distancia_ojos < 1:
        return None

    centro_ojos_x = (ojo_izquierdo[0] + ojo_derecho[0]) / 2
    desplazamiento_nariz = (nariz[0] - centro_ojos_x) / distancia_ojos

    distancia_nariz_ojo_izq = float(np.linalg.norm(nariz - ojo_izquierdo))
    distancia_nariz_ojo_der = float(np.linalg.norm(nariz - ojo_derecho))
    suma_distancias = distancia_nariz_ojo_izq + distancia_nariz_ojo_der

    if suma_distancias < 1:
        return None

    asimetria = (
        distancia_nariz_ojo_izq - distancia_nariz_ojo_der
    ) / suma_distancias

    return 0.65 * desplazamiento_nariz + 0.35 * asimetria


def pose_en_pantalla(pose):
    """Devuelve la instrucción que acompaña a la flecha."""
    if pose in ("izquierda", "derecha"):
        return "gira siguiendo la flecha"
    return "mira de frente a la cámara"


class RegistroRostro:
    """Ventana de captura guiada para registrar un usuario de la base de datos."""

    def __init__(self, parent, id_usuario, al_completar=None):
        self.parent = parent
        self.id_usuario = int(id_usuario)
        self.al_completar = al_completar
        self.es_ventana_principal = parent is None
        self.root = tk.Tk() if parent is None else tk.Toplevel(parent)

        self.terminado = False
        self.guardando = False
        self.persistencia_incierta = False
        self.puede_reintentar_guardado = False
        self.muestras = []
        self.ids_insertados = []
        self.contador_cuadros = 0
        self.fallos_lectura = 0
        self.caracteristica_actual = None
        self.rostros_actuales = []
        self.rostro_actual = None
        self.pose_correcta = False
        self.historial_giro = []
        self.cuadros_pose_estable = 0
        self.giro_frontal_referencia = None
        self.imagen_tk = None
        self.camara = None
        self.usuario = None

        self.root.title("Registro facial")
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.configurar_ventana()

        if not self.cargar_datos():
            return

        if not self.abrir_camara():
            return

        self.crear_interfaz()

        if parent is not None:
            self.root.transient(parent)
            self.root.grab_set()

        self.root.after(30, self.actualizar_video)

    def configurar_ventana(self):
        ancho_pantalla = self.root.winfo_screenwidth()
        alto_pantalla = self.root.winfo_screenheight()

        ancho = min(820, max(680, ancho_pantalla - 30))
        alto = min(720, max(580, alto_pantalla - 50))
        x = max(0, (ancho_pantalla - ancho) // 2)
        y = max(0, (alto_pantalla - alto) // 2)

        self.root.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.root.minsize(680, 580)

    def cerrar_por_error(self):
        """Cierra esta ventana después de mostrar un error de inicialización."""
        self.terminado = True

        if self.camara is not None:
            self.camara.release()
            self.camara = None

        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def cargar_datos(self):
        """Comprueba modelos, usuario activo y ausencia de muestras anteriores."""
        for ruta in (YUNET, SFACE):
            if not ruta.is_file():
                messagebox.showerror(
                    "Falta un modelo",
                    f"No encuentro el archivo del modelo:\n{ruta}",
                    parent=self.root,
                )
                self.cerrar_por_error()
                return False

        try:
            self.usuario = obtener_permisos_por_usuario(self.id_usuario)
            if self.usuario is None:
                messagebox.showerror(
                    "Usuario no encontrado",
                    f"No existe un usuario con ID {self.id_usuario}.",
                    parent=self.root,
                )
                self.cerrar_por_error()
                return False

            if not self.usuario.get("activo"):
                messagebox.showerror(
                    "Usuario inactivo",
                    "Solo se puede registrar el rostro de un usuario activo.",
                    parent=self.root,
                )
                self.cerrar_por_error()
                return False

            muestras_existentes = leer_embeddings_usuario(self.id_usuario)
            if muestras_existentes:
                messagebox.showwarning(
                    "El usuario ya tiene registro facial",
                    (
                        f"{self.usuario['nombre']} ya tiene "
                        f"{len(muestras_existentes)} muestra(s) registrada(s).\n\n"
                        "No se reemplazaron. Elimina las muestras anteriores "
                        "antes de iniciar un nuevo registro."
                    ),
                    parent=self.root,
                )
                self.cerrar_por_error()
                return False

        except Exception as error:
            messagebox.showerror(
                "No se pudo consultar la base de datos",
                f"Verifica la conexión y los permisos de MySQL.\n\n{error}",
                parent=self.root,
            )
            self.cerrar_por_error()
            return False

        try:
            self.detector = cv2.FaceDetectorYN.create(
                str(YUNET),
                "",
                (320, 320),
                0.8,
                0.3,
                5000,
            )
            self.reconocedor = cv2.FaceRecognizerSF.create(str(SFACE), "")
        except cv2.error as error:
            messagebox.showerror(
                "No se pudieron cargar los modelos faciales",
                str(error),
                parent=self.root,
            )
            self.cerrar_por_error()
            return False

        return True

    def abrir_camara(self):
        """Abre la cámara mediante el módulo compartido del proyecto."""
        self.camara = Camera(index=0, width=640, height=480, fps=30)

        if not self.camara.open():
            messagebox.showerror(
                "Cámara no disponible",
                self.camara.last_error or "No se pudo abrir la cámara.",
                parent=self.root,
            )
            self.cerrar_por_error()
            return False

        return True

    def crear_interfaz(self):
        contenedor = ttk.Frame(self.root, padding=12)
        contenedor.pack(fill="both", expand=True)

        ttk.Label(
            contenedor,
            text="Registro facial",
            font=("TkDefaultFont", 18, "bold"),
        ).pack(pady=(0, 3))

        nombre_usuario = self.usuario.get("nombre", "Usuario")
        ttk.Label(
            contenedor,
            text=(
                f"Usuario: {nombre_usuario} · ID {self.id_usuario}\n"
                "Sigue la pose indicada y captura cada muestra."
            ),
            justify="center",
        ).pack(pady=(0, 8))

        fila_pose = ttk.Frame(contenedor)
        fila_pose.pack(fill="x", pady=(0, 5))

        self.flecha_pose = tk.Canvas(
            fila_pose,
            width=72,
            height=52,
            background=self.root.cget("background"),
            highlightthickness=0,
        )
        self.flecha_pose.pack(side="left", padx=(0, 8))

        self.pose_var = tk.StringVar(
            value=f"Muestra 1 de {MAX_MUESTRAS} · Mira de frente"
        )
        ttk.Label(
            fila_pose,
            textvariable=self.pose_var,
            font=("TkDefaultFont", 13, "bold"),
            anchor="w",
            justify="left",
        ).pack(side="left", fill="x", expand=True)

        self.actualizar_flecha_pose(SECUENCIA_POSES[0])

        self.video_label = ttk.Label(
            contenedor,
            text="Iniciando cámara…",
            anchor="center",
        )
        self.video_label.pack(pady=3)

        self.estado_var = tk.StringVar(value="Colócate frente a la cámara.")
        ttk.Label(
            contenedor,
            textvariable=self.estado_var,
            font=("TkDefaultFont", 11, "bold"),
            anchor="center",
            justify="center",
            wraplength=780,
        ).pack(fill="x", pady=(5, 3))

        self.progreso_var = tk.StringVar(
            value=f"0 de {MAX_MUESTRAS} muestras"
        )
        ttk.Label(
            contenedor,
            textvariable=self.progreso_var,
        ).pack(pady=(2, 0))

        self.barra = ttk.Progressbar(
            contenedor,
            maximum=MAX_MUESTRAS,
            value=0,
            mode="determinate",
        )
        self.barra.pack(fill="x", pady=(3, 8))

        botones = ttk.Frame(contenedor)
        botones.pack(pady=3)

        self.boton_capturar = ttk.Button(
            botones,
            text=f"Capturar muestra 1/{MAX_MUESTRAS}",
            command=self.capturar_muestra,
            state="disabled",
        )
        self.boton_capturar.pack(side="left", padx=5, ipadx=12, ipady=4)

        ttk.Button(
            botones,
            text="Cancelar",
            command=self.cerrar,
        ).pack(side="left", padx=5, ipadx=8, ipady=4)

    def actualizar_flecha_pose(self, pose):
        """Dibuja las flechas invertidas para coincidir con la vista de cámara."""
        self.flecha_pose.delete("all")

        # La imagen de la cámara se percibe en espejo:
        # izquierda lógica apunta a la derecha de la pantalla, y viceversa.
        if pose == "derecha":
            inicio, fin = (58, 26), (12, 26)
        elif pose == "izquierda":
            inicio, fin = (14, 26), (60, 26)
        else:
            inicio, fin = (36, 43), (36, 7)

        self.flecha_pose.create_line(
            *inicio,
            *fin,
            fill="#1769aa",
            width=5,
            arrow=tk.LAST,
            arrowshape=(12, 15, 7),
            capstyle=tk.ROUND,
        )

    def procesar_cuadro(self, imagen):
        """Detecta el rostro, valida la posición y calcula su embedding."""
        alto, ancho = imagen.shape[:2]
        self.detector.setInputSize((ancho, alto))
        _, rostros = self.detector.detect(imagen)

        self.rostro_actual = None
        self.rostros_actuales = [] if rostros is None else list(rostros)
        self.caracteristica_actual = None
        self.pose_correcta = False

        indicaciones = evaluar_calidad(imagen, self.rostros_actuales)
        if indicaciones:
            self.historial_giro.clear()
            self.cuadros_pose_estable = 0
            self.estado_var.set(indicaciones[0])
            return

        if len(self.muestras) >= MAX_MUESTRAS:
            return

        self.rostro_actual = self.rostros_actuales[0]
        pose_esperada = SECUENCIA_POSES[len(self.muestras)]
        indice = calcular_indice_giro(self.rostro_actual)

        if indice is None:
            self.historial_giro.clear()
            self.cuadros_pose_estable = 0
            pose_en_rango = False
            self.estado_var.set(
                "No pude confirmar el giro automáticamente. "
                "Si ya estás en la posición indicada, puedes capturar."
            )
        else:
            self.historial_giro.append(indice)
            if len(self.historial_giro) > VENTANA_GIRO:
                self.historial_giro.pop(0)

            indice_suavizado = float(np.median(self.historial_giro))

            if self.giro_frontal_referencia is None:
                giro_relativo = indice_suavizado
                pose_en_rango = (
                    pose_esperada == "frente"
                    and abs(giro_relativo) <= UMBRAL_POSE_FRONTAL
                )
            else:
                giro_relativo = indice_suavizado - self.giro_frontal_referencia

                if pose_esperada == "frente":
                    pose_en_rango = abs(giro_relativo) <= UMBRAL_POSE_FRONTAL
                elif pose_esperada == "izquierda":
                    pose_en_rango = giro_relativo <= -UMBRAL_POSE_LATERAL
                else:
                    pose_en_rango = giro_relativo >= UMBRAL_POSE_LATERAL

        if not pose_en_rango:
            self.cuadros_pose_estable = 0

            if pose_esperada == "frente":
                instruccion = "Mira de frente a la cámara."
            else:
                instruccion = "Gira un poco siguiendo la flecha."

            self.estado_var.set(
                f"{instruccion} Si ya estás en esa posición, pulsa Capturar."
            )
        else:
            self.cuadros_pose_estable += 1

            if self.cuadros_pose_estable < CUADROS_POSE_ESTABLE:
                faltan = CUADROS_POSE_ESTABLE - self.cuadros_pose_estable
                self.estado_var.set(
                    f"Pose detectada. Mantenla un momento ({faltan})."
                )
                return

        try:
            cara_alineada = self.reconocedor.alignCrop(
                imagen,
                self.rostro_actual,
            )
            caracteristica = self.reconocedor.feature(cara_alineada)

            if caracteristica is None or caracteristica.size == 0:
                raise ValueError("El modelo no generó una característica facial.")

            self.caracteristica_actual = np.asarray(
                caracteristica,
                dtype=np.float32,
            ).flatten()

            if not np.all(np.isfinite(self.caracteristica_actual)):
                self.caracteristica_actual = None
                raise ValueError("El embedding contiene valores inválidos.")

        except (cv2.error, ValueError) as error:
            self.caracteristica_actual = None
            self.estado_var.set(f"No pude procesar el rostro: {error}")
            return

        self.pose_correcta = pose_en_rango

        if pose_en_rango:
            self.estado_var.set(
                "Pose correcta. Pulsa Capturar para guardar esta muestra."
            )

    def actualizar_boton(self):
        if not hasattr(self, "boton_capturar"):
            return

        if self.guardando:
            self.boton_capturar.configure(state="disabled")
            return

        if len(self.muestras) >= MAX_MUESTRAS:
            puede_guardar = (
                self.puede_reintentar_guardado
                and not self.persistencia_incierta
                and not self.terminado
            )
            self.boton_capturar.configure(
                state="normal" if puede_guardar else "disabled",
                text="Reintentar guardado",
                command=self.guardar_en_base_de_datos,
            )
            return

        listo = (
            self.caracteristica_actual is not None
            and not self.terminado
            and not self.persistencia_incierta
        )
        siguiente = len(self.muestras) + 1

        self.boton_capturar.configure(
            state="normal" if listo else "disabled",
            text=f"Capturar muestra {siguiente}/{MAX_MUESTRAS}",
            command=self.capturar_muestra,
        )

    def actualizar_video(self):
        if self.terminado:
            return

        imagen = self.camara.read_frame()

        if imagen is None:
            self.fallos_lectura += 1
            self.caracteristica_actual = None
            self.actualizar_boton()

            if self.fallos_lectura >= MAX_FALLOS_CAMARA:
                self.estado_var.set(
                    "La cámara dejó de enviar imagen. "
                    "Revisa la conexión y vuelve a iniciar el registro."
                )
                self.boton_capturar.configure(state="disabled")
                return

            self.root.after(100, self.actualizar_video)
            return

        self.fallos_lectura = 0
        self.contador_cuadros += 1

        if (
            len(self.muestras) < MAX_MUESTRAS
            and self.contador_cuadros % PROCESAR_CADA == 0
        ):
            self.procesar_cuadro(imagen)

        for rostro in self.rostros_actuales:
            x, y, ancho, alto = map(int, rostro[:4])
            color = (
                (0, 180, 0)
                if len(self.rostros_actuales) == 1 and self.pose_correcta
                else (0, 165, 255)
            )
            cv2.rectangle(
                imagen,
                (x, y),
                (x + ancho, y + alto),
                color,
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

        self.actualizar_boton()
        self.root.after(15, self.actualizar_video)

    def capturar_muestra(self):
        """Agrega a la sesión la muestra que está lista en pantalla."""
        if (
            self.terminado
            or self.caracteristica_actual is None
            or len(self.muestras) >= MAX_MUESTRAS
        ):
            return

        muestra = np.asarray(
            self.caracteristica_actual,
            dtype=np.float32,
        ).flatten()

        if muestra.size == 0 or not np.all(np.isfinite(muestra)):
            self.estado_var.set("La muestra no es válida. Intenta de nuevo.")
            return

        self.muestras.append(muestra)
        cantidad = len(self.muestras)

        self.progreso_var.set(f"{cantidad} de {MAX_MUESTRAS} muestras")
        self.barra.configure(value=cantidad)
        self.caracteristica_actual = None
        self.pose_correcta = False

        if cantidad == 1 and self.historial_giro:
            self.giro_frontal_referencia = float(
                np.median(self.historial_giro)
            )

        self.historial_giro.clear()
        self.cuadros_pose_estable = 0
        self.actualizar_boton()

        if cantidad < MAX_MUESTRAS:
            pose_siguiente = SECUENCIA_POSES[cantidad]
            instruccion = pose_en_pantalla(pose_siguiente)

            self.pose_var.set(
                f"Muestra {cantidad + 1} de {MAX_MUESTRAS} · "
                f"{instruccion.capitalize()}"
            )
            self.actualizar_flecha_pose(pose_siguiente)
            self.estado_var.set(
                f"Muestra {cantidad} capturada. Ahora {instruccion}."
            )
            return

        self.pose_var.set("Guardando muestras en la base de datos…")
        self.estado_var.set("Espera mientras se guardan las muestras.")
        self.puede_reintentar_guardado = False
        self.guardar_en_base_de_datos()

    def guardar_en_base_de_datos(self):
        """Guarda los embeddings y revierte los nuevos si una inserción falla."""
        if (
            self.guardando
            or self.terminado
            or len(self.muestras) != MAX_MUESTRAS
            or self.persistencia_incierta
        ):
            return

        self.guardando = True
        self.actualizar_boton()
        ids_nuevos = []

        try:
            for muestra in self.muestras:
                embedding_bytes = muestra.astype(np.float32).tobytes()
                id_embedding = insertar_embedding(
                    self.id_usuario,
                    embedding_bytes,
                    MODELO_EMBEDDING,
                )
                ids_nuevos.append(id_embedding)

        except Exception as error:
            errores_reversion = []

            for id_embedding in reversed(ids_nuevos):
                try:
                    eliminar_embedding(id_embedding)
                except Exception as error_reversion:
                    errores_reversion.append(
                        f"ID {id_embedding}: {error_reversion}"
                    )

            if errores_reversion:
                self.persistencia_incierta = True
                self.puede_reintentar_guardado = False
                detalle_reversion = "\n".join(errores_reversion)
                mensaje = (
                    f"No se completó el registro: {error}\n\n"
                    "No pude eliminar todas las muestras parciales. "
                    "Revisa esos registros en la base de datos antes de volver "
                    f"a intentarlo:\n{detalle_reversion}"
                )
            else:
                self.puede_reintentar_guardado = True
                mensaje = (
                    f"No se pudieron guardar las muestras:\n{error}\n\n"
                    "Las inserciones parciales se revirtieron. "
                    "Puedes pulsar «Reintentar guardado»."
                )

            self.estado_var.set("No se completó el guardado.")
            self.guardando = False
            self.actualizar_boton()
            messagebox.showerror(
                "Error al guardar el registro",
                mensaje,
                parent=self.root,
            )
            return

        self.ids_insertados = ids_nuevos
        self.puede_reintentar_guardado = False
        self.guardando = False
        self.terminado = True

        self.pose_var.set("Registro completo")
        self.flecha_pose.delete("all")
        self.estado_var.set(
            f"Se guardaron cinco muestras para {self.usuario['nombre']}."
        )
        self.actualizar_boton()

        if self.camara is not None:
            self.camara.release()
            self.camara = None

        messagebox.showinfo(
            "Registro completado",
            (
                f"Se guardaron cinco muestras faciales para "
                f"{self.usuario['nombre']}."
            ),
            parent=self.root,
        )

        if self.al_completar is not None:
            try:
                self.al_completar(self.id_usuario)
            except Exception as error:
                print(f"[REGISTRO FACIAL] Error en callback: {error}")

    def cerrar(self):
        if self.terminado:
            self.cerrar_por_error()
            return

        if self.muestras:
            salir = messagebox.askyesno(
                "Cancelar registro",
                (
                    "Las muestras capturadas que aún no se guardaron "
                    "se perderán. ¿Quieres salir?"
                ),
                parent=self.root,
            )
            if not salir:
                return

        self.cerrar_por_error()


def abrir_registro_rostro(parent, id_usuario, al_completar=None):
    """Abre la ventana desde otra pantalla del programa."""
    return RegistroRostro(
        parent=parent,
        id_usuario=id_usuario,
        al_completar=al_completar,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Registro facial guiado para un usuario existente."
    )
    parser.add_argument(
        "--id-usuario",
        type=int,
        help="ID del usuario existente en MySQL.",
    )
    argumentos = parser.parse_args()

    id_usuario = argumentos.id_usuario
    if id_usuario is None:
        try:
            id_usuario = int(input("ID del usuario existente: ").strip())
        except ValueError:
            raise SystemExit("El ID debe ser un número entero.")

    app = RegistroRostro(parent=None, id_usuario=id_usuario)
    if not app.terminado:
        app.root.mainloop()


if __name__ == "__main__":
    main()