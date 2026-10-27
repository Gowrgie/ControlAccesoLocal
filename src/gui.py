"""GUI module: the Tkinter screens of the access control system.

Flow: Standby -> Role selection -> Login -> Validation -> Result -> Standby.

InterfazControlAcceso only draws screens and reacts to them. Capture, presence
and hardware are inherited from access_flow.ControlAcceso and reached through
self.hardware; validation comes from access_logic.

Tkinter is optional so the program can start without a desktop: when it is
missing, tk, ttk and messagebox are None and Main_code.py uses physical mode.
"""
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError:
    tk = ttk = messagebox = None
import atexit
import time
from datetime import datetime

from access_flow import ControlAcceso
from access_logic import validar_acceso_por_rol
from audio import reproducir_sonido_exito, reproducir_sonido_error, reproducir_sonido_alerta
from reconocimiento_facial.reconocer_rostro import abrir_reconocimiento
from hardware import PIR_PIN


class InterfazControlAcceso(ControlAcceso):
    """Graphical interface for the local access control system."""
    puede_facial = True
    ventana_facial = None

    def __init__(self, root):
        self.root = root
        self.root.title("Control de Acceso Local")
        self.root.geometry("800x480")  # Typical Raspberry Pi resolution
        self.root.configure(bg="#f0f0f0")

        self.preparar_estado()
        # Reserve the hardware before configuring pins.
        self.hardware.crear_lock()

        self.hardware.configurar_gpio()
        print(f"Sensor PIR configurado en GPIO {PIR_PIN}")

        self.hardware.inicializar_hardware()

        # Release the lock when closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        atexit.register(self.hardware.limpiar_lock)

        # State variables
        self.rol_seleccionado = None
        self.identificador = ""
        self.contrasena = ""
        self.timeout_pir = 30  # seconds of inactivity
        self.ultimo_movimiento = time.time()

        # System colors
        self.COLOR_PRIMARY = "#1a5490"
        self.COLOR_SUCCESS = "#27ae60"
        self.COLOR_DANGER = "#e74c3c"
        self.COLOR_WARNING = "#f39c12"
        self.COLOR_BG = "#ecf0f1"
        self.COLOR_TEXT = "#2c3e50"

        # Main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Start on the standby screen
        self.mostrar_standby()
        self.leer_botones()

    # ============ hooks required by ControlAcceso ============
    def anunciar_sistema_listo(self):
        self.hardware.tono_buzzer(.15)
        self.root.deiconify()
        self.root.lift()

    def notificar_error_hardware(self, error):
        if messagebox is not None:
            messagebox.showerror("Error de hardware", str(error))

    # ============ standby and presence ============
    def mostrar_standby(self):
        """Initial screen with the PIR sensor - Wireframe: 01_standby.png"""
        self.limpiar_frame()
        self.reiniciar_estado_espera()

        # Centered main frame
        frame = ttk.Frame(self.main_frame)
        frame.pack(fill=tk.BOTH, expand=True)

        # Title
        titulo = tk.Label(
            frame,
            text="SISTEMA DE CONTROL DE ACCESO",
            font=("Helvetica", 28, "bold"),
            fg=self.COLOR_PRIMARY,
            bg=self.COLOR_BG
        )
        titulo.pack(pady=60)

        # PIR status
        self.pir_label = tk.Label(
            frame,
            text="Detectando presencia...",
            font=("Helvetica", 16),
            fg=self.COLOR_WARNING,
            bg=self.COLOR_BG
        )
        self.pir_label.pack(pady=40)

        # Visual activity indicator
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

        # Instruction (updated when movement is detected)
        self.instruccion_label = tk.Label(
            frame,
            text="Acérquese para continuar",
            font=("Helvetica", 12),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_BG,
            justify=tk.CENTER
        )
        self.instruccion_label.pack(pady=30)

        # Space key (only works while the PIR is active)
        self.root.bind("<space>", self.validar_entrada_space)

        # Start reading the PIR sensor
        self.leer_pir()

    def leer_pir(self):
        """Updates the screen using the same retained presence as the buttons."""
        self.actualizar_presencia(time.monotonic())
        movimiento_detectado = self.pir_activo

        if movimiento_detectado:
            self.pir_canvas.itemconfig(self.pir_circulo, fill=self.COLOR_SUCCESS)
            self.pir_label.config(text="Presencia detectada", fg=self.COLOR_SUCCESS)
            self.instruccion_label.config(
                text="Presencia detectada\nPresione ESPACIO para continuar",
                fg=self.COLOR_SUCCESS
            )
        else:
            self.pir_canvas.itemconfig(self.pir_circulo, fill="#d0d0d0")
            self.pir_label.config(text="Detectando presencia...", fg=self.COLOR_WARNING)
            self.instruccion_label.config(
                text="Acérquese para continuar",
                fg=self.COLOR_TEXT
            )

        # Keep reading every 500 ms
        self._pir_after = self.root.after(500, self.leer_pir)

    def validar_entrada_space(self, event):
        """Checks whether the user can move on when pressing space"""
        if self._captura_metodo in ("botones", "facial") or self._en_resultado:
            return "break"
        self.actualizar_presencia(time.monotonic())
        if not self.pir_activo:
            # No movement detected
            self.pir_label.config(text="Acérquese, por favor", fg=self.COLOR_DANGER)
            return "break"  # Ignore the event

        # With movement, move on
        self._captura_metodo = "interfaz_grafica"
        print("[MÉTODO] Pantalla seleccionada; botones físicos en espera.", flush=True)
        self.mostrar_seleccion_rol()
        return "break"
    
    # ============ facial recognition ============
    def iniciar_reconocimiento_facial(self):
        from reconocimiento_facial.reconocer_rostro import abrir_reconocimiento
        self.ventana_facial = abrir_reconocimiento(
            self.root,
            callback_identificacion=self.procesar_identificacion_facial,
            callback_cancelacion=self.cancelar_facial,
            callback_error=self.fallo_facial,
        )

    def cerrar_reconocimiento_facial(self):
        if self.ventana_facial is not None:
            self.ventana_facial.cerrar()

    # ============ role selection ============
    def mostrar_seleccion_rol(self):
        """Role selection screen - Wireframe: 02_login_user.png"""
        self.limpiar_frame()

        frame = ttk.Frame(self.main_frame)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        titulo = tk.Label(
            frame,
            text="Seleccione su rol",
            font=("Helvetica", 24, "bold"),
            fg=self.COLOR_PRIMARY,
            bg=self.COLOR_BG
        )
        titulo.pack(pady=30)

        desc = tk.Label(
            frame,
            text="Seleccione el tipo de usuario para continuar",
            font=("Helvetica", 12),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_BG
        )
        desc.pack(pady=10)

        # Buttons frame
        botones_frame = ttk.Frame(frame)
        botones_frame.pack(pady=40, fill=tk.BOTH, expand=True)

        self.crear_boton_rol(botones_frame, "USUARIO GENERAL", "general", 0)
        self.crear_boton_rol(botones_frame, "SERVICIO TECNICO", "technical", 1)
        self.crear_boton_rol(botones_frame, "ADMINISTRADOR", "admin", 2)

        # Back button
        btn_atras = tk.Button(
            frame,
            text="<- Atras",
            font=("Helvetica", 10),
            bg="#95a5a6",
            fg="white",
            command=self.mostrar_standby,
            padx=10,
            pady=5
        )
        btn_atras.pack(side=tk.LEFT, pady=20)

    def crear_boton_rol(self, parent, texto, rol, column):
        """Creates a role selection button"""
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
        """Stores the selected role and moves on"""
        self._captura_metodo = "interfaz_grafica"
        self.rol_seleccionado = rol
        self.mostrar_login()

    # ============ login and validation from the screen ============
    def mostrar_login(self):
        """Login screen by role - Wireframes: 03, 04, 05"""
        self.limpiar_frame()

        frame = ttk.Frame(self.main_frame)
        frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)

        rol_texto = {
            "general": "USUARIO GENERAL",
            "technical": "SERVICIO TECNICO",
            "admin": "ADMINISTRADOR"
        }

        titulo = tk.Label(
            frame,
            text=f"Login - {rol_texto.get(self.rol_seleccionado, 'Usuario')}",
            font=("Helvetica", 20, "bold"),
            fg=self.COLOR_PRIMARY,
            bg=self.COLOR_BG
        )
        titulo.pack(pady=20)

        input_frame = ttk.Frame(frame)
        input_frame.pack(pady=20)

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
            show="*"
        )
        self.entry_pass.grid(row=1, column=1, padx=10, pady=10)

        # Enter key sends the form
        self.entry_id.bind("<Return>", lambda e: self.entry_pass.focus())
        self.entry_pass.bind("<Return>", lambda e: self.validar_login())

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
        """Validates the credentials against the database"""
        if self._captura_metodo == "botones" or self._en_resultado:
            return
        self.identificador = self.entry_id.get().strip()
        self.contrasena = self.entry_pass.get()

        # Basic validation
        if not self.identificador or not self.contrasena:
            messagebox.showwarning("Error", "Complete todos los campos")
            return

        resultado = validar_acceso_por_rol(
            self.identificador, self.contrasena, self.rol_seleccionado
        )

        if self.rol_seleccionado == "admin" and resultado == "autorizado":
            self.mostrar_menu_registro_admin()
            return

        self.mostrar_resultado(resultado)

    def mostrar_menu_registro_admin(self):
        """Permite al administrador elegir un usuario activo para inscribir."""
        try:
            from scripts_db.db_conexion import listar_usuarios_activos
            usuarios = listar_usuarios_activos()
        except Exception as error:
            messagebox.showerror(
                "Error",
                f"No se pudieron cargar los usuarios:\n{error}",
                parent=self.root,
            )
            self.mostrar_standby()
            return

        self.usuarios_registro = usuarios
        self.limpiar_frame()

        frame = ttk.Frame(self.main_frame, padding=24)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame,
            text="Registro facial",
            font=("Helvetica", 24, "bold"),
            fg=self.COLOR_PRIMARY,
            bg=self.COLOR_BG,
        ).pack(pady=(30, 12))

        tk.Label(
            frame,
            text="Selecciona un usuario activo para iniciar su inscripción.",
            font=("Helvetica", 13),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_BG,
        ).pack(pady=10)

        opciones = [
            f"{usuario['nombre']} ({usuario['identificador']})"
            for usuario in usuarios
        ]

        self.selector_usuario_registro = ttk.Combobox(
            frame,
            values=opciones,
            state="readonly",
            width=42,
        )
        self.selector_usuario_registro.pack(pady=15)

        if opciones:
            self.selector_usuario_registro.current(0)
        else:
            tk.Label(
                frame,
                text="No hay usuarios activos para registrar.",
                font=("Helvetica", 12),
                fg=self.COLOR_TEXT,
                bg=self.COLOR_BG,
            ).pack(pady=10)

        tk.Button(
            frame,
            text="Iniciar registro",
            font=("Helvetica", 12, "bold"),
            bg=self.COLOR_SUCCESS,
            fg="white",
            command=self.iniciar_registro_admin,
            state="normal" if usuarios else "disabled",
            padx=18,
            pady=8,
        ).pack(pady=10)

        tk.Button(
            frame,
            text="Cancelar",
            font=("Helvetica", 11),
            bg="#95a5a6",
            fg="white",
            command=self.mostrar_standby,
            padx=18,
            pady=6,
        ).pack(pady=5)
        
    def iniciar_registro_admin(self):
        """Abre la captura guiada para el usuario seleccionado."""
        indice = self.selector_usuario_registro.current()
        if indice < 0:
            messagebox.showwarning(
                "Selecciona un usuario",
                "Elige un usuario antes de iniciar el registro.",
                parent=self.root,
            )
            return

        usuario = self.usuarios_registro[indice]

        try:
            from reconocimiento_facial.registrar_rostro import abrir_registro_rostro

            self.ventana_registro_rostro = abrir_registro_rostro(
                parent=self.root,
                id_usuario=usuario["id_usuario"],
                al_completar=self.registro_finalizado,
            )
        except Exception as error:
            self.ventana_registro_rostro = None
            messagebox.showerror(
                "No se pudo iniciar el registro",
                str(error),
                parent=self.root,
            )
            self.mostrar_standby()

    # ============ result shared by both methods ============
    def mostrar_resultado(self, resultado, accionar=True):
        """Shows the validation result - Wireframes: 06, 07"""
        self._en_resultado = True
        if accionar:
            self.hardware.respuesta_hardware(resultado)
        self.limpiar_frame()

        frame = ttk.Frame(self.main_frame)
        frame.pack(fill=tk.BOTH, expand=True)

        # Appearance depends on the result
        resultados = {
            "autorizado": {
                "color": self.COLOR_SUCCESS,
                "simbolo": "[OK]",
                "titulo": "ACCESO CONCEDIDO",
                "mensaje": f"Bienvenido\n{self.identificador}",
                "icono_color": "#27ae60",
                "sonido": reproducir_sonido_exito
            },
            "sin_permiso": {
                "color": self.COLOR_DANGER,
                "simbolo": "[X]",
                "titulo": "ACCESO DENEGADO",
                "mensaje": "Usuario sin permisos",
                "icono_color": "#e74c3c",
                "sonido": reproducir_sonido_error
            },
            "no_reconocido": {
                "color": self.COLOR_DANGER,
                "simbolo": "[X]",
                "titulo": "ACCESO DENEGADO",
                "mensaje": "Usuario no reconocido",
                "icono_color": "#e74c3c",
                "sonido": reproducir_sonido_error
            },
            "error_sistema": {
                "color": self.COLOR_WARNING,
                "simbolo": "[!]",
                "titulo": "ERROR DEL SISTEMA",
                "mensaje": "Intente mas tarde",
                "icono_color": "#f39c12",
                "sonido": reproducir_sonido_alerta
            }
        }

        config = resultados.get(resultado, resultados["no_reconocido"])

        # Play the sound for this result
        if "sonido" in config:
            config["sonido"]()

        icono = tk.Label(
            frame,
            text=config["simbolo"],
            font=("Helvetica", 100, "bold"),
            fg=config["icono_color"],
            bg=self.COLOR_BG
        )
        icono.pack(pady=40)

        titulo = tk.Label(
            frame,
            text=config["titulo"],
            font=("Helvetica", 28, "bold"),
            fg=config["icono_color"],
            bg=self.COLOR_BG
        )
        titulo.pack(pady=10)

        mensaje = tk.Label(
            frame,
            text=config["mensaje"],
            font=("Helvetica", 16),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_BG,
            justify=tk.CENTER
        )
        mensaje.pack(pady=20)

        hora = tk.Label(
            frame,
            text=datetime.now().strftime("%H:%M:%S"),
            font=("Helvetica", 12),
            fg="#7f8c8d",
            bg=self.COLOR_BG
        )
        hora.pack(pady=10)

        # Restart automatically in 4 seconds
        self.programar_accion(4000, self.mostrar_standby)

    # ============ screen helpers ============
    def limpiar_frame(self):
        """Clears the content of the main frame"""
        if self._pir_after is not None:
            self.root.after_cancel(self._pir_after)
            self._pir_after = None
        # Cancel the reading before destroying its widgets to avoid the
        # "invalid command name" error on a deleted canvas.
        # Unbind Space so it does not change screens during login.
        self.root.unbind("<space>")

        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def registro_finalizado(self, id_usuario=None):
        self.ventana_registro_rostro = None
        try:
            self.root.after_idle(self.mostrar_standby)
        except tk.TclError:
            pass

    def cancelar_facial(self):
        """Libera el intento facial cancelado y vuelve a la espera."""
        if self._cerrando or self._en_resultado:
            return

        print("[FACIAL] Reconocimiento cancelado.", flush=True)
        self.mostrar_standby()

    def fallo_facial(self, mensaje):
        """Informa el error y deja disponibles los métodos alternativos."""
        if self._cerrando:
            return

        print(f"[FACIAL] Error en el reconocedor: {mensaje}", flush=True)
        self.puede_facial = False
        self.mostrar_standby()

        if messagebox is not None:
            messagebox.showerror(
                "Reconocimiento facial",
                mensaje,
                parent=self.root,
            )