"""

Requisitos:
- tkinter (incluido en Python)
- mysql-connector-python
- RPi.GPIO (para sensor PIR real en Raspberry Pi)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime
import sys
import os
import atexit

# Importar RPi.GPIO para sensor PIR
import RPi.GPIO as GPIO

# Ruta del archivo lock para coordinación entre interfaz.py y Main_code.py
LOCK_FILE = "/tmp/control_acceso.lock"
LOCK_IDENTIFIER = "interfaz_grafica"

# Configuración del sensor PIR
PIR_PIN = 27  # GPIO 27

# Importar el módulo de conexión a base de datos
# Asegúrate de que scripts_db esté en el mismo directorio o en PYTHONPATH
try:
    from scripts_db.db_conexion import validar_acceso
except ImportError:
    print("Advertencia: No se pudo importar db_conexion. Modo prueba desactivado.")
    validar_acceso = None


class InterfazControlAcceso:
    """
    Interfaz gráfica para Sistema de Control de Acceso Local
    Flujo: Standby -> Selección Rol -> Login -> Validación -> Resultado -> Standby
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Control de Acceso Local")
        self.root.geometry("800x480")  # Resolución típica para Raspberry Pi
        self.root.configure(bg="#f0f0f0")

        # Crear lock para coordinación con Main_code.py
        self.crear_lock()

        # Configurar sensor PIR
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIR_PIN, GPIO.IN)
        print(f"Sensor PIR configurado en GPIO {PIR_PIN}")

        # Registrar limpieza del lock al cerrar
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        atexit.register(self.limpiar_lock)

        # Variables de estado
        self.rol_seleccionado = None
        self.identificador = ""
        self.contrasena = ""
        self.pir_activo = False
        self.timeout_pir = 30  # segundos de inactividad
        self.ultimo_movimiento = time.time()

        # Colores del sistema
        self.COLOR_PRIMARY = "#1a5490"
        self.COLOR_SUCCESS = "#27ae60"
        self.COLOR_DANGER = "#e74c3c"
        self.COLOR_WARNING = "#f39c12"
        self.COLOR_BG = "#ecf0f1"
        self.COLOR_TEXT = "#2c3e50"

        # Crear frame principal
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Iniciar en pantalla de standby
        self.mostrar_standby()

    # ============ SISTEMA DE LOCK ============
    def crear_lock(self):
        """Crea archivo lock. Si ya existe, significa que Main_code.py está corriendo."""
        try:
            if os.path.exists(LOCK_FILE):
                with open(LOCK_FILE, 'r') as f:
                    contenido = f.read().strip()
                if contenido == "botones":
                    messagebox.showerror(
                        "Sistema en uso",
                        "La interfaz de botones está activa.\nNo se puede usar la interfaz gráfica simultáneamente."
                    )
                    sys.exit(1)

            # Crear el lock
            with open(LOCK_FILE, 'w') as f:
                f.write(LOCK_IDENTIFIER)
            print(f"Lock creado: {LOCK_FILE}")
        except Exception as e:
            print(f"⚠ Error al crear lock: {e}")

    def limpiar_lock(self):
        """Elimina el archivo lock al cerrar."""
        try:
            if os.path.exists(LOCK_FILE):
                with open(LOCK_FILE, 'r') as f:
                    if f.read().strip() == LOCK_IDENTIFIER:
                        os.remove(LOCK_FILE)
                        print(f"Lock eliminado: {LOCK_FILE}")
        except Exception as e:
            print(f"Error al limpiar lock: {e}")

    def on_closing(self):
        """Maneja el cierre de la ventana."""
        self.limpiar_lock()
        GPIO.cleanup()
        print("GPIO limpiado")
        self.root.destroy()

    # ============ PANTALLA DE STANDBY ============
    def mostrar_standby(self):
        """Pantalla inicial con sensor PIR - Wireframe: 01_standby.png"""
        self.limpiar_frame()

        # Frame principal centrado
        frame = ttk.Frame(self.main_frame)
        frame.pack(fill=tk.BOTH, expand=True)

        # Logo/Título
        titulo = tk.Label(
            frame,
            text="SISTEMA DE CONTROL DE ACCESO",
            font=("Helvetica", 28, "bold"),
            fg=self.COLOR_PRIMARY,
            bg=self.COLOR_BG
        )
        titulo.pack(pady=60)

        # Estado PIR
        self.pir_label = tk.Label(
            frame,
            text="Detectando presencia...",
            font=("Helvetica", 16),
            fg=self.COLOR_WARNING,
            bg=self.COLOR_BG
        )
        self.pir_label.pack(pady=40)

        # Indicador visual de actividad
        self.pir_canvas = tk.Canvas(
            frame,
            width=100,
            height=100,
            bg=self.COLOR_BG,
            highlightthickness=0
        )
        self.pir_canvas.pack(pady=40)
        self.pir_circulo = self.pir_canvas.create_oval(
            25, 25, 75, 75,
            fill="#d0d0d0",
            outline=self.COLOR_PRIMARY,
            width=3
        )

        # Instrucción
        instruccion = tk.Label(
            frame,
            text="Acérquese para continuar\n(o presione cualquier botón)",
            font=("Helvetica", 12),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_BG,
            justify=tk.CENTER
        )
        instruccion.pack(pady=30)

        # Simular detección de movimiento del PIR
        self.simular_pir()

        # Permitir inicio manual (para demostración)
        self.root.bind("<space>", lambda e: self.mostrar_seleccion_rol())

    def simular_pir(self):
        """Lee el sensor PIR real"""
        # Leer estado del GPIO 27 (HIGH=1 cuando detecta movimiento)
        movimiento_detectado = GPIO.input(PIR_PIN) == GPIO.HIGH

        # Actualizar interfaz según detección
        if movimiento_detectado:
            self.pir_canvas.itemconfig(self.pir_circulo, fill=self.COLOR_SUCCESS)
            self.pir_label.config(text="Presencia detectada", fg=self.COLOR_SUCCESS)
        else:
            self.pir_canvas.itemconfig(self.pir_circulo, fill="#d0d0d0")
            self.pir_label.config(text="Detectando presencia...", fg=self.COLOR_WARNING)

        # Continuar lectura
        self.root.after(500, self.simular_pir)

    # ============ PANTALLA DE SELECCIÓN DE ROL ============
    def mostrar_seleccion_rol(self):
        """Pantalla de selección de rol/usuario - Wireframe: 02_login_user.png"""
        self.limpiar_frame()

        frame = ttk.Frame(self.main_frame)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Título
        titulo = tk.Label(
            frame,
            text="Seleccione su rol",
            font=("Helvetica", 24, "bold"),
            fg=self.COLOR_PRIMARY,
            bg=self.COLOR_BG
        )
        titulo.pack(pady=30)

        # Descripción
        desc = tk.Label(
            frame,
            text="Seleccione el tipo de usuario para continuar",
            font=("Helvetica", 12),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_BG
        )
        desc.pack(pady=10)

        # Frame de botones
        botones_frame = ttk.Frame(frame)
        botones_frame.pack(pady=40, fill=tk.BOTH, expand=True)

        # Botón Estudiante
        self.crear_boton_rol(
            botones_frame,
            "ESTUDIANTE",
            "student",
            0
        )

        # Botón Técnico
        self.crear_boton_rol(
            botones_frame,
            "SERVICIO TECNICO",
            "technical",
            1
        )

        # Botón Admin
        self.crear_boton_rol(
            botones_frame,
            "ADMINISTRADOR",
            "admin",
            2
        )

        # Botón Atrás
        btn_atras = tk.Button(
            frame,
            text="← Atrás",
            font=("Helvetica", 10),
            bg="#95a5a6",
            fg="white",
            command=self.mostrar_standby,
            padx=10,
            pady=5
        )
        btn_atras.pack(side=tk.LEFT, pady=20)

    def crear_boton_rol(self, parent, texto, rol, column):
        """Crea un botón de selección de rol"""
        btn = tk.Button(
            parent,
            text=texto,
            font=("Helvetica", 14, "bold"),
            bg=self.COLOR_PRIMARY,
            fg="white",
            command=lambda: self.seleccionar_rol(rol),
            height=4,
            width=20
        )
        btn.grid(row=0, column=column, padx=10, pady=10, sticky="nsew")
        parent.grid_columnconfigure(column, weight=1)

    def seleccionar_rol(self, rol):
        """Registra la selección de rol y avanza"""
        self.rol_seleccionado = rol
        self.mostrar_login()

    # ============ PANTALLA DE LOGIN ============
    def mostrar_login(self):
        """Pantalla de login por rol - Wireframes: 03, 04, 05"""
        self.limpiar_frame()

        frame = ttk.Frame(self.main_frame)
        frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)

        # Determinar etiqueta según rol
        rol_texto = {
            "student": "ESTUDIANTE",
            "technical": "SERVICIO TÉCNICO",
            "admin": "ADMINISTRADOR"
        }

        # Título con rol
        titulo = tk.Label(
            frame,
            text=f"Login - {rol_texto.get(self.rol_seleccionado, 'Usuario')}",
            font=("Helvetica", 20, "bold"),
            fg=self.COLOR_PRIMARY,
            bg=self.COLOR_BG
        )
        titulo.pack(pady=20)

        # Frame para inputs
        input_frame = ttk.Frame(frame)
        input_frame.pack(pady=20)

        # Identificador
        tk.Label(
            input_frame,
            text="Identificador:",
            font=("Helvetica", 12),
            bg=self.COLOR_BG
        ).grid(row=0, column=0, sticky="w", pady=10)

        self.entry_id = tk.Entry(
            input_frame,
            font=("Helvetica", 14),
            width=20
        )
        self.entry_id.grid(row=0, column=1, padx=10, pady=10)
        self.entry_id.focus()

        # Contraseña
        tk.Label(
            input_frame,
            text="Contraseña:",
            font=("Helvetica", 12),
            bg=self.COLOR_BG
        ).grid(row=1, column=0, sticky="w", pady=10)

        self.entry_pass = tk.Entry(
            input_frame,
            font=("Helvetica", 14),
            width=20,
            show="•"
        )
        self.entry_pass.grid(row=1, column=1, padx=10, pady=10)

        # Vincular Enter para enviar
        self.entry_id.bind("<Return>", lambda e: self.entry_pass.focus())
        self.entry_pass.bind("<Return>", lambda e: self.validar_login())

        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=30)

        tk.Button(
            btn_frame,
            text="Validar",
            font=("Helvetica", 12, "bold"),
            bg=self.COLOR_SUCCESS,
            fg="white",
            command=self.validar_login,
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame,
            text="Cancelar",
            font=("Helvetica", 12),
            bg="#95a5a6",
            fg="white",
            command=self.mostrar_seleccion_rol,
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=10)

    def validar_login(self):
        """Valida credenciales contra la base de datos"""
        self.identificador = self.entry_id.get().strip()
        self.contrasena = self.entry_pass.get()

        # Validación básica
        if not self.identificador or not self.contrasena:
            messagebox.showwarning("Error", "Complete todos los campos")
            return

        # Validar contra BD
        if validar_acceso:
            resultado = validar_acceso(
                self.identificador,
                self.contrasena,
                "interfaz_grafica"
            )
            self.mostrar_resultado(resultado)
        else:
            # Modo prueba sin BD
            messagebox.showinfo("Modo Prueba", "Base de datos no disponible")
            self.mostrar_resultado("autorizado")

    # ============ PANTALLA DE RESULTADO ============
    def mostrar_resultado(self, resultado):
        """Muestra resultado de validación - Wireframes: 06, 07"""
        self.limpiar_frame()

        frame = ttk.Frame(self.main_frame)
        frame.pack(fill=tk.BOTH, expand=True)

        # Determinar apariencia según resultado
        resultados = {
            "autorizado": {
                "color": self.COLOR_SUCCESS,
                "emoji": "[OK]",
                "titulo": "ACCESO CONCEDIDO",
                "mensaje": f"Bienvenido\n{self.identificador}",
                "icono_color": "#27ae60"
            },
            "sin_permiso": {
                "color": self.COLOR_DANGER,
                "emoji": "[X]",
                "titulo": "ACCESO DENEGADO",
                "mensaje": "Usuario sin permisos",
                "icono_color": "#e74c3c"
            },
            "no_reconocido": {
                "color": self.COLOR_DANGER,
                "emoji": "[X]",
                "titulo": "ACCESO DENEGADO",
                "mensaje": "Usuario no reconocido",
                "icono_color": "#e74c3c"
            },
            "error_sistema": {
                "color": self.COLOR_WARNING,
                "emoji": "[!]",
                "titulo": "ERROR DEL SISTEMA",
                "mensaje": "Intente mas tarde",
                "icono_color": "#f39c12"
            }
        }

        config = resultados.get(resultado, resultados["no_reconocido"])

        # Icono grande
        icono = tk.Label(
            frame,
            text=config["emoji"],
            font=("Helvetica", 100, "bold"),
            fg=config["icono_color"],
            bg=self.COLOR_BG
        )
        icono.pack(pady=40)

        # Título
        titulo = tk.Label(
            frame,
            text=config["titulo"],
            font=("Helvetica", 28, "bold"),
            fg=config["icono_color"],
            bg=self.COLOR_BG
        )
        titulo.pack(pady=10)

        # Mensaje
        mensaje = tk.Label(
            frame,
            text=config["mensaje"],
            font=("Helvetica", 16),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_BG,
            justify=tk.CENTER
        )
        mensaje.pack(pady=20)

        # Hora del intento
        hora = tk.Label(
            frame,
            text=datetime.now().strftime("%H:%M:%S"),
            font=("Helvetica", 12),
            fg="#7f8c8d",
            bg=self.COLOR_BG
        )
        hora.pack(pady=10)

        # Reiniciar automáticamente en 4 segundos
        self.root.after(4000, self.mostrar_standby)

    # ============ UTILIDADES ============
    def limpiar_frame(self):
        """Limpia el contenido del frame principal"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()


def main():
    """
    Función principal

    NOTAS IMPORTANTES:

    1. Sistema de Lock:
       Main_code.py debe implementar el mismo sistema para evitar conflictos:
       - Al iniciar: crear /tmp/control_acceso.lock con contenido "botones"
       - Al cerrar: eliminar /tmp/control_acceso.lock
       - Si el lock contiene "interfaz_grafica", esperar o abortar

    2. Sensor PIR:
       - Requiere RPi.GPIO instalado
       - Lee el GPIO 27 (sensor PIR real)
       - El sensor PIR debe estar conectado a GPIO 27
    """
    root = tk.Tk()
    app = InterfazControlAcceso(root)
    root.mainloop()


if __name__ == "__main__":
    main()