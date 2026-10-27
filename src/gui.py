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
from audio import reproducir_mensaje_resultado
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
                text="ESPACIO: interfaz | Presione un botón: acceso físico\nReconocimiento facial inicia en 2 segundos",
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
        if self._captura_metodo in ("botones", "facial", "administracion") or self._en_resultado:
            return "break"

        self.actualizar_presencia(time.monotonic())
        if not self.pir_activo:
            self.pir_label.config(text="Acérquese, por favor", fg=self.COLOR_DANGER)
            return "break"

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
            self.mostrar_menu_administrador()
            return

        self.mostrar_resultado(resultado)

    def mostrar_menu_registro_admin(self):
        """Menú de administración de usuarios y registros faciales."""
        self.limpiar_frame()
        self._en_resultado = False
        self._captura_metodo = "administracion"
        self._captura_id = ""
        self._captura_clave = ""

        frame = ttk.Frame(self.main_frame, padding=24)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Administración de usuarios",
            font=("Helvetica", 22, "bold"),
        ).pack(pady=(35, 20))

        ttk.Button(
            frame,
            text="Registrar rostro de un usuario existente",
            command=self.mostrar_usuarios_para_registro_admin,
        ).pack(pady=10)

        ttk.Button(
            frame,
            text="Crear usuario nuevo",
            command=self.mostrar_formulario_usuario_nuevo,
        ).pack(pady=10)

        ttk.Button(
            frame,
            text="Volver",
            command=self.mostrar_standby,
        ).pack(pady=(25, 10))


    def mostrar_usuarios_para_registro_admin(self):
        """Muestra los usuarios activos y señala cuáles ya tienen rostro."""
        try:
            from scripts_db.db_conexion import listar_usuarios_activos
            from scripts_db.database import leer_embeddings_usuario

            usuarios = listar_usuarios_activos()
            for usuario in usuarios:
                usuario["tiene_rostro"] = bool(
                    leer_embeddings_usuario(usuario["id_usuario"])
                )
        except Exception as error:
            messagebox.showerror(
                "Error",
                f"No se pudieron cargar los usuarios:\n{error}",
                parent=self.root,
            )
            self.mostrar_menu_registro_admin()
            return

        self.usuarios_registro = usuarios
        self.limpiar_frame()

        frame = ttk.Frame(self.main_frame, padding=24)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Registro facial de usuario existente",
            font=("Helvetica", 20, "bold"),
        ).pack(pady=(25, 12))

        ttk.Label(
            frame,
            text="Los usuarios que ya tienen muestras no se pueden registrar otra vez.",
        ).pack(pady=8)

        opciones = []
        for usuario in usuarios:
            estado = " — rostro ya registrado" if usuario["tiene_rostro"] else ""
            opciones.append(
                f"{usuario['nombre']} ({usuario['identificador']}){estado}"
            )

        self.selector_usuario_registro = ttk.Combobox(
            frame,
            values=opciones,
            state="readonly",
            width=55,
        )
        self.selector_usuario_registro.pack(pady=15)

        if opciones:
            self.selector_usuario_registro.current(0)
        else:
            ttk.Label(frame, text="No hay usuarios activos.").pack(pady=10)

        ttk.Button(
            frame,
            text="Iniciar registro facial",
            command=self.iniciar_registro_admin,
            state="normal" if usuarios else "disabled",
        ).pack(pady=8)

        ttk.Button(
            frame,
            text="Volver",
            command=self.mostrar_menu_registro_admin,
        ).pack(pady=8)


    def iniciar_registro_admin(self):
        """Abre el registro facial para el usuario seleccionado."""
        indice = self.selector_usuario_registro.current()

        if indice < 0:
            messagebox.showwarning(
                "Selecciona un usuario",
                "Elige un usuario antes de iniciar el registro.",
                parent=self.root,
            )
            return

        usuario = self.usuarios_registro[indice]

        if usuario["tiene_rostro"]:
            messagebox.showwarning(
                "Registro facial existente",
                (
                    f"{usuario['nombre']} ya tiene muestras faciales. "
                    "No se inició otro registro."
                ),
                parent=self.root,
            )
            return

        self.abrir_registro_rostro_admin(usuario["id_usuario"])


    def mostrar_formulario_usuario_nuevo(self):
        """Muestra el formulario para crear una cuenta."""
        try:
            from scripts_db.db_conexion import listar_roles
            roles = listar_roles()
        except Exception as error:
            messagebox.showerror(
                "Error",
                f"No se pudieron cargar los roles:\n{error}",
                parent=self.root,
            )
            self.mostrar_menu_registro_admin()
            return

        if not roles:
            messagebox.showerror(
                "Sin roles",
                "No hay roles disponibles para asignar al usuario.",
                parent=self.root,
            )
            self.mostrar_menu_registro_admin()
            return

        self.limpiar_frame()

        frame = ttk.Frame(self.main_frame, padding=24)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Crear usuario",
            font=("Helvetica", 20, "bold"),
        ).grid(row=0, column=0, columnspan=2, pady=(10, 20))

        ttk.Label(frame, text="Nombre:").grid(
            row=1, column=0, sticky="e", padx=8, pady=8
        )
        entrada_nombre = ttk.Entry(frame, width=32)
        entrada_nombre.grid(row=1, column=1, padx=8, pady=8)

        ttk.Label(frame, text="Identificador:").grid(
            row=2, column=0, sticky="e", padx=8, pady=8
        )
        entrada_identificador = ttk.Entry(frame, width=32)
        entrada_identificador.grid(row=2, column=1, padx=8, pady=8)

        ttk.Label(frame, text="Contraseña:").grid(
            row=3, column=0, sticky="e", padx=8, pady=8
        )
        entrada_clave = ttk.Entry(frame, width=32, show="*")
        entrada_clave.grid(row=3, column=1, padx=8, pady=8)

        ttk.Label(frame, text="Rol:").grid(
            row=4, column=0, sticky="e", padx=8, pady=8
        )
        selector_rol = ttk.Combobox(
            frame,
            values=[rol["nombre_rol"] for rol in roles],
            state="readonly",
            width=29,
        )
        selector_rol.grid(row=4, column=1, padx=8, pady=8)
        selector_rol.current(0)

        registrar_rostro_ahora = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame,
            text="Registrar el rostro ahora",
            variable=registrar_rostro_ahora,
        ).grid(row=5, column=0, columnspan=2, pady=12)

        def guardar_usuario():
            indice_rol = selector_rol.current()
            if indice_rol < 0:
                messagebox.showwarning(
                    "Selecciona un rol",
                    "Elige el rol del usuario.",
                    parent=self.root,
                )
                return

            try:
                from scripts_db.db_conexion import crear_usuario

                id_usuario = crear_usuario(
                    nombre=entrada_nombre.get(),
                    identificador=entrada_identificador.get(),
                    clave_acceso=entrada_clave.get(),
                    id_rol=roles[indice_rol]["id_rol"],
                )
            except ValueError as error:
                messagebox.showwarning(
                    "No se pudo crear el usuario",
                    str(error),
                    parent=self.root,
                )
                return
            except Exception as error:
                messagebox.showerror(
                    "Error al crear el usuario",
                    str(error),
                    parent=self.root,
                )
                return

            if registrar_rostro_ahora.get():
                self.abrir_registro_rostro_admin(id_usuario)
                return

            messagebox.showinfo(
                "Usuario creado",
                "La cuenta se creó. Puedes registrar su rostro después.",
                parent=self.root,
            )
            self.mostrar_menu_registro_admin()
        ttk.Button(
            frame,
            text="Crear usuario",
            command=guardar_usuario,
        ).grid(row=6, column=0, padx=8, pady=16, sticky="e")

        ttk.Button(
            frame,
            text="Cancelar",
            command=self.mostrar_menu_registro_admin,
        ).grid(row=6, column=1, padx=8, pady=16, sticky="w")


    def abrir_registro_rostro_admin(self, id_usuario):
        """Abre la captura guiada para un usuario existente o recién creado."""
        try:
            from reconocimiento_facial.registrar_rostro import abrir_registro_rostro

            self.ventana_registro_rostro = abrir_registro_rostro(
                parent=self.root,
                id_usuario=id_usuario,
                al_completar=self.registro_finalizado,
            )
        except Exception as error:
            self.ventana_registro_rostro = None
            messagebox.showerror(
                "No se pudo iniciar el registro facial",
                str(error),
                parent=self.root,
            )
            # La cuenta ya creada se conserva, aunque no se abra la cámara.
            self.mostrar_menu_registro_admin()

    # ============ result shared by both methods ============
    def mostrar_resultado(self, resultado, accionar=True, al_finalizar=None):
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
                
            },
            "sin_permiso": {
                "color": self.COLOR_DANGER,
                "simbolo": "[X]",
                "titulo": "ACCESO DENEGADO",
                "mensaje": "Usuario sin permisos",
                "icono_color": "#e74c3c",
                
            },
            "no_reconocido": {
                "color": self.COLOR_DANGER,
                "simbolo": "[X]",
                "titulo": "ACCESO DENEGADO",
                "mensaje": "Usuario no reconocido",
                "icono_color": "#e74c3c",
                
            },
            "error_sistema": {
                "color": self.COLOR_WARNING,
                "simbolo": "[!]",
                "titulo": "ERROR DEL SISTEMA",
                "mensaje": "Intente mas tarde",
                "icono_color": "#f39c12",
                
            }
        }

        config = resultados.get(resultado, resultados["no_reconocido"])

        # Play the sound for this result
        reproducir_mensaje_resultado(resultado)

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

        destino = al_finalizar or self.mostrar_standby
        self.programar_accion(4000, destino)

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
        """Vuelve al menú de administración al cerrar la captura facial."""
        self.ventana_registro_rostro = None
        try:
            self.root.after_idle(self.mostrar_menu_registro_admin)
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

    def mostrar_menu_administrador(self, id_usuario=None):
        """Muestra la confirmación existente y después abre el menú."""
        if id_usuario is not None:
            self.id_administrador_actual = id_usuario
            self.identificador = "Administrador"

        self.ventana_facial = None
        self._captura_metodo = "administracion"
        self.mostrar_resultado(
            "autorizado",
            accionar=True,
            al_finalizar=self.mostrar_menu_registro_admin,
        )