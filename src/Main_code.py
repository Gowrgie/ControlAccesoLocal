# SISTEMA DE CONTROL DE ACCESO: INTERFAZ Y BOTONES EN UN SOLO PROGRAMA
#
# Flujo: estabilizar PIR -> esperar presencia -> capturar por un método
# -> consultar MySQL -> indicar resultado y mover servo -> volver al reposo.
#
# Ejecución con interfaz o respaldo automático:
#   ~/control-acceso-env/bin/python ~/PI2.1.py
# Ejecución exclusivamente física, incluso desde SSH:
#   ~/control-acceso-env/bin/python ~/PI2.1.py --solo-botones
#
# Dependencias adicionales: lgpio y las funciones de scripts_db/db_conexion.py.
# Los tonos de audio requieren speaker-test; el buzzer GPIO es independiente.
# En Ubuntu, tkinter puede requerir instalar el paquete python3-tk.
#
"""
Requisitos:
- tkinter (incluido en Python)
- mysql-connector-python
- RPi.GPIO (para sensor PIR real en Raspberry Pi)
"""

# ============ 1. IMPORTACIONES Y DEPENDENCIAS ============
# Tkinter es opcional para poder arrancar en modo físico sin escritorio.
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError:
    tk = ttk = messagebox = None
import threading
import time
from datetime import datetime
import sys
import os
import atexit
import subprocess
import lgpio
import fcntl
import argparse
import heapq
import itertools
import unicodedata

# Importar RPi.GPIO para sensor PIR
import RPi.GPIO as GPIO

# ============ 2. CONFIGURACIÓN GENERAL Y BASE DE DATOS ============
# El bloqueo impide dos instancias de ESTE programa sobre los mismos GPIO.
# No ejecutar simultáneamente los antiguos programas independientes.
LOCK_FILE = "/tmp/control_acceso.lock"
LOCK_IDENTIFIER = "interfaz_grafica"

# Configuración del sensor PIR
PIR_PIN = 27  # GPIO 27

# Importar el módulo de conexión a base de datos
# Asegúrate de que scripts_db esté en el mismo directorio o en PYTHONPATH
try:
    from scripts_db.db_conexion import validar_acceso, buscar_usuario, registrar_intento
except ImportError:
    print("Error: No se pudo importar db_conexion. No se autorizarán accesos.")
    validar_acceso = buscar_usuario = registrar_intento = None


# ============ 3. VALIDACIÓN DE USUARIOS Y ROLES ============
# Se reutiliza el módulo de DB sin modificar sus archivos.
def normalizar_rol(nombre):
    # Permite comparar "Servicio técnico" y "servicio_tecnico" sin diferencias
    # de acentos, mayúsculas o separadores.
    texto = unicodedata.normalize("NFKD", str(nombre or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.lower().replace("_", " ").split())


def validar_acceso_por_rol(identificador, clave, rol_seleccionado):
    """Usa las funciones existentes de DB y registra una sola decisión final."""
    if buscar_usuario is None or registrar_intento is None:
        return "error_sistema"
    try:
        usuario = buscar_usuario(identificador, clave)
        id_usuario = None
        if usuario is None:
            resultado = "no_reconocido"
        else:
            id_usuario = usuario["id_usuario"]
            rol_real = normalizar_rol(usuario["nombre_rol"])
            rol_pedido = {"general": "usuario general", "technical": "servicio tecnico",
                          "admin": "administrador"}.get(rol_seleccionado)
            # El administrador puede elegir cualquier rol, pero también necesita
            # permiso de apertura. Los demás solo pueden elegir su propio rol.
            es_admin = (rol_real == "administrador" and bool(usuario["permiso_administracion"]))
            if not usuario["permiso_apertura"] or rol_pedido is None:
                resultado = "sin_permiso"
            elif es_admin or (rol_real == rol_pedido and rol_pedido != "administrador"):
                resultado = "autorizado"
            else:
                resultado = "sin_permiso"
        # Registrar después de comprobar el rol evita guardar una autorización
        # que en realidad debería rechazarse. No llamar aquí a validar_acceso:
        # esa función también registra, y duplicaría el intento.
        registrar_intento(id_usuario, "interfaz_grafica", resultado)
        return resultado
    except Exception as error:
        print("Error al validar usuario y rol:", error, flush=True)
        return "error_sistema"


# ============ 4. AUDIO POR ALTAVOCES ============
# Estas funciones usan la salida de audio de Ubuntu, no el buzzer del GPIO 25.
# Si speaker-test o la salida de audio no están disponibles, pueden no sonar.
def reproducir_tono(frecuencia=1000, duracion=0.5):
    """Genera un tono usando speaker-test."""
    try:
        os.system(f'(speaker-test -t sine -f {frecuencia} -l 1 & sleep {duracion}; killall speaker-test) 2>/dev/null &')
    except:
        pass


def reproducir_sonido_exito():
    """Reproduce sonido de acceso concedido - dos tonos ascendentes."""
    reproducir_tono(1000, 0.3)
    time.sleep(0.1)
    reproducir_tono(1200, 0.3)


def reproducir_sonido_error():
    """Reproduce sonido de acceso denegado - dos tonos descendentes."""
    reproducir_tono(600, 0.2)
    time.sleep(0.1)
    reproducir_tono(400, 0.2)


def reproducir_sonido_alerta():
    """Reproduce sonido de alerta del sistema."""
    reproducir_tono(800, 0.25)
    time.sleep(0.15)
    reproducir_tono(600, 0.25)


# ============ 5. INTERFAZ ORIGINAL Y ESTADO COMPARTIDO ============
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

        self.preparar_estado()
        # Reservar el hardware antes de configurar pines.
        self.crear_lock()

        # Configurar sensor PIR
        self._gpio_iniciado = True
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIR_PIN, GPIO.IN)
        print(f"Sensor PIR configurado en GPIO {PIR_PIN}")

        self.inicializar_hardware()

        # Registrar limpieza del lock al cerrar
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        atexit.register(self.limpiar_lock)

        # Variables de estado
        self.rol_seleccionado = None
        self.identificador = ""
        self.contrasena = ""
        self.pir_activo = False  # Bandera para rastrear si hay movimiento
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
        self.leer_botones()

    def preparar_estado(self):
        # Se usa tanto con ventana como en modo físico: ambos comparten las
        # mismas reglas de captura, presencia, exclusión y limpieza.
        self._lock_handle = None
        self._servo_chip = None
        self._gpio_iniciado = False
        self._cerrando = False
        # None: ambos métodos disponibles. Un método elegido reserva el intento.
        self._captura_metodo = None
        self._captura_fase = "identificador"
        self._captura_id = ""
        self._captura_clave = ""
        self._ultima_pulsacion = 0.0
        self._botones_anteriores = set()
        self._diagnostico_pir = None
        # Plazo de presencia retenida; no es el temporizador entre pulsaciones.
        self._presencia_hasta = 0.0
        self._boton_crudo = None
        self._boton_cambio = 0.0
        self._boton_estable = None
        self._esperar_liberacion = True
        self._inicio_listo = False
        self._hardware_inicio = time.monotonic()
        self._hardware_armado = False
        self._en_resultado = False
        self._hardware_after = None
        self._pir_after = None
        # Guardar los temporizadores permite cancelarlos al cerrar la aplicación.
        self._acciones_after = set()

    # ============ 5.1 BLOQUEO Y CIERRE DE LA APLICACIÓN ============
    def crear_lock(self):
        # La instancia unificada es la única propietaria de los GPIO.
        self._lock_handle = open(LOCK_FILE, "a+")
        try:
            fcntl.flock(self._lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._lock_handle.close()
            self._lock_handle = None
            raise RuntimeError("El sistema de acceso ya está activo.")
        self._lock_handle.seek(0)
        self._lock_handle.truncate()
        self._lock_handle.write(LOCK_IDENTIFIER)
        self._lock_handle.flush()

    def limpiar_lock(self):
        # No se elimina el archivo: se libera el bloqueo del proceso.
        if self._lock_handle is not None:
            self._lock_handle.seek(0)
            self._lock_handle.truncate()
            self._lock_handle.close()
            self._lock_handle = None

    def on_closing(self):
        if self._cerrando:
            return
        self._cerrando = True
        for token in [self._pir_after, self._hardware_after, *self._acciones_after]:
            if token:
                try:
                    self.root.after_cancel(token)
                except Exception:
                    pass
        self.cerrar_hardware()
        self.limpiar_lock()
        self.root.destroy()

    # ============ 5.2 PANTALLA DE ESPERA Y PRESENCIA ============
    def mostrar_standby(self):
        """Pantalla inicial con sensor PIR - Wireframe: 01_standby.png"""
        self.limpiar_frame()
        if self._en_resultado:
            lgpio.tx_servo(self._servo_chip, 26, 1500)
        self._en_resultado = False
        self._captura_metodo = None
        self._captura_id = ""
        self._captura_clave = ""
        self._hardware_armado = False
        self._presencia_hasta = 0.0
        self._esperar_liberacion = True
        self.pir_activo = False  # Reiniciar estado del PIR

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

        # Instrucción (se actualiza cuando se detecta movimiento)
        self.instruccion_label = tk.Label(
            frame,
            text="Acérquese para continuar",
            font=("Helvetica", 12),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_BG,
            justify=tk.CENTER
        )
        self.instruccion_label.pack(pady=30)

        # Vincular tecla espacio (solo funcionará si PIR está activo)
        self.root.bind("<space>", self.validar_entrada_space)

        # Iniciar lectura del sensor PIR
        self.leer_pir()

    def leer_pir(self):
        """Actualiza la pantalla usando la misma presencia retenida que los botones."""
        self.actualizar_presencia(time.monotonic())
        movimiento_detectado = self.pir_activo

        # Actualizar estado interno y interfaz
        if movimiento_detectado:
            self.pir_activo = True
            self.pir_canvas.itemconfig(self.pir_circulo, fill=self.COLOR_SUCCESS)
            self.pir_label.config(text="Presencia detectada", fg=self.COLOR_SUCCESS)
            self.instruccion_label.config(
                text="Presencia detectada\nPresione ESPACIO para continuar",
                fg=self.COLOR_SUCCESS
            )
        else:
            self.pir_activo = False
            self.pir_canvas.itemconfig(self.pir_circulo, fill="#d0d0d0")
            self.pir_label.config(text="Detectando presencia...", fg=self.COLOR_WARNING)
            self.instruccion_label.config(
                text="Acérquese para continuar",
                fg=self.COLOR_TEXT
            )

        # Continuar lectura cada 500ms
        self._pir_after = self.root.after(500, self.leer_pir)

    def validar_entrada_space(self, event):
        """Valida si se puede avanzar al presionar espacio"""
        if self._captura_metodo == "botones":
            return "break"
        self.actualizar_presencia(time.monotonic())
        if not self.pir_activo:
            # No hay movimiento detectado
            self.pir_label.config(text="Acérquese, por favor", fg=self.COLOR_DANGER)
            return "break"  # Ignorar el evento

        # Si hay movimiento, avanzar
        self._captura_metodo = "interfaz_grafica"
        print("[MÉTODO] Pantalla seleccionada; botones físicos en espera.", flush=True)
        self.mostrar_seleccion_rol()
        return "break"

    # ============ 5.3 SELECCIÓN DE ROL ============
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

        # Botón Usuario General
        self.crear_boton_rol(
            botones_frame,
            "USUARIO GENERAL",
            "general",
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
        self._captura_metodo = "interfaz_grafica"
        self.rol_seleccionado = rol
        self.mostrar_login()

    # ============ 5.4 CAPTURA Y VALIDACIÓN DESDE LA PANTALLA ============
    def mostrar_login(self):
        """Pantalla de login por rol - Wireframes: 03, 04, 05"""
        self.limpiar_frame()

        frame = ttk.Frame(self.main_frame)
        frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)

        # Determinar etiqueta según rol
        rol_texto = {
            "general": "USUARIO GENERAL",
            "technical": "SERVICIO TECNICO",
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
            show="*"
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
        if self._captura_metodo == "botones" or self._en_resultado:
            return
        self.identificador = self.entry_id.get().strip()
        self.contrasena = self.entry_pass.get()

        # Validación básica
        if not self.identificador or not self.contrasena:
            messagebox.showwarning("Error", "Complete todos los campos")
            return

        resultado = validar_acceso_por_rol(
            self.identificador, self.contrasena, self.rol_seleccionado
        )
        self.mostrar_resultado(resultado)

    # ============ 5.5 RESULTADO COMPARTIDO POR AMBOS MÉTODOS ============
    def mostrar_resultado(self, resultado, accionar=True):
        """Muestra resultado de validación - Wireframes: 06, 07"""
        self._en_resultado = True
        if accionar:
            self.respuesta_hardware(resultado)
        self.limpiar_frame()

        frame = ttk.Frame(self.main_frame)
        frame.pack(fill=tk.BOTH, expand=True)

        # Determinar apariencia según resultado
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

        # Reproducir sonido según resultado
        if "sonido" in config:
            config["sonido"]()

        # Icono grande
        icono = tk.Label(
            frame,
            text=config["simbolo"],
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
        self.programar_accion(4000, self.mostrar_standby)

    # ============ 6. PINES, SERVO, LEDS Y BUZZER ============
    def inicializar_hardware(self):
        # Numeración BCM (GPIO), no posición física en el conector:
        # botones 1/2/3: 14/15/18; PIR: 27; verde: 23; rojo: 24;
        # buzzer: 25; servo: 26. PULL_UP implica pulsado = LOW.
        self._pines_botones = {14: "1", 15: "2", 18: "3"}
        for pin in self._pines_botones:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        for pin in (23, 24, 25):
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        self._servo_chip = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(self._servo_chip, 26, 0)
        self._servo_reclamado = True
        lgpio.tx_servo(self._servo_chip, 26, 1500)
        print("Estabilizando PIR para botones: 30 segundos.")

    def programar_accion(self, milisegundos, funcion):
        # Se programa una acción sin dormir el hilo de la interfaz.
        # root.after también existe en nuestro temporizador del modo físico.
        def ejecutar():
            self._acciones_after.discard(token)
            if not self._cerrando:
                funcion()
        token = self.root.after(milisegundos, ejecutar)
        self._acciones_after.add(token)

    def tono_buzzer(self, duracion):
        GPIO.output(25, GPIO.HIGH)
        self.programar_accion(int(duracion * 1000), lambda: GPIO.output(25, GPIO.LOW))

    def respuesta_hardware(self, resultado):
        # Pulsos aproximados del servo: 1000 us = rechazo (0°),
        # 1500 us = reposo (90°), 2000 us = apertura (180°).
        # La apertura dura 3 s; el rechazo vuelve al reposo al finalizar
        # la pantalla de resultado (4 s), mediante mostrar_standby.
        if resultado == "autorizado":
            pin = 23
            lgpio.tx_servo(self._servo_chip, 26, 2000)
            self.programar_accion(3000, lambda: lgpio.tx_servo(self._servo_chip, 26, 1500))
        else:
            pin = 24
            if resultado in ("sin_permiso", "no_reconocido"):
                # Misma posición de rechazo del Main físico original: 0 grados.
                lgpio.tx_servo(self._servo_chip, 26, 1000)
            else:
                lgpio.tx_servo(self._servo_chip, 26, 1500)
        GPIO.output(pin, GPIO.HIGH)
        self.programar_accion(1000, lambda: GPIO.output(pin, GPIO.LOW))
        if resultado == "error_sistema":
            self.tono_buzzer(1.0)
        else:
            self.tono_buzzer(0.1)
            self.programar_accion(170, lambda: self.tono_buzzer(0.1))
            self.programar_accion(340, lambda: self.tono_buzzer(0.1))

    def anunciar_sistema_listo(self):
        self.tono_buzzer(.15)
        self.root.deiconify()
        self.root.lift()

    # ============ 7. ESTABILIZACIÓN Y PRESENCIA RETENIDA ============
    def actualizar_presencia(self, ahora):
        # monotonic mide intervalos sin depender de ajustes del reloj del sistema.
        presencia = GPIO.input(PIR_PIN) == GPIO.HIGH
        if presencia != self._diagnostico_pir:
            print("[PIR]", "PRESENCIA (HIGH)" if presencia else "REPOSO (LOW)", flush=True)
            self._diagnostico_pir = presencia
        if self._en_resultado or self._captura_metodo is not None:
            # Una captura ya iniciada no depende de que el PIR siga activo.
            return
        # No habilitar la captura hasta cumplir 30 s Y observar el PIR en LOW.
        # Solo entonces se muestra la ventana y suena el aviso de sistema listo.
        if ahora - self._hardware_inicio < 30:
            self.pir_activo = False
            return
        if not presencia and not self._hardware_armado:
            self._hardware_armado = True
            print("[LISTO] Sensor estabilizado y en reposo. Esperando presencia.", flush=True)
            if not self._inicio_listo:
                self._inicio_listo = True
                self.anunciar_sistema_listo()
        # Mientras el PIR esté HIGH se renueva el plazo. Tras volver a LOW,
        # quedan 4 s para empezar por pantalla o botones; al iniciar la captura,
        # la presencia deja de ser un requisito para terminar ese intento.
        if presencia and self._hardware_armado:
            self._presencia_hasta = ahora + 4.0
        activo = ahora < self._presencia_hasta
        if activo != self.pir_activo:
            print("[PRESENCIA]", "Habilitada para pantalla y botones" if activo
                  else "Ventana de 4 segundos terminada", flush=True)
        self.pir_activo = activo

    # ============ 8. BOTONES: ANTIRREBOTE Y CAPTURA ============
    def detectar_pulsacion(self, bajos, ahora):
        """Exige 30 ms estables tanto al pulsar como al soltar.

        Un botón sostenido cuenta una vez. Dos botones juntos no se ordenan
        artificialmente: se ignoran hasta que todos se suelten.
        """
        for pin in sorted(bajos - self._botones_anteriores):
            print(f"[BOTÓN {self._pines_botones[pin]} / GPIO {pin}] PRESIONADO (LOW)", flush=True)
        for pin in sorted(self._botones_anteriores - bajos):
            print(f"[BOTÓN {self._pines_botones[pin]} / GPIO {pin}] LIBERADO (HIGH)", flush=True)
        self._botones_anteriores = set(bajos)
        crudo = next(iter(bajos)) if len(bajos) == 1 else ("varios" if bajos else None)
        if crudo != self._boton_crudo:
            self._boton_crudo = crudo
            self._boton_cambio = ahora
            if crudo == "varios":
                self._esperar_liberacion = True
                print("[IGNORADO] Varios botones a la vez. Suelte todos antes de continuar.", flush=True)
        # Un cambio eléctrico breve no cuenta: debe mantenerse 30 ms.
        # También exigimos soltar de forma estable antes de aceptar otro dígito.
        if ahora - self._boton_cambio < .030:
            return None
        self._boton_estable = crudo
        if crudo is None:
            self._esperar_liberacion = False
            return None
        if crudo == "varios" or self._esperar_liberacion:
            return None
        self._esperar_liberacion = True
        return crudo

    def cancelar_captura_fisica(self):
        print("[CANCELADO] 4 segundos sin pulsación. Identificador y clave descartados.", flush=True)
        GPIO.output(24, GPIO.HIGH)
        self.tono_buzzer(.25)
        self.programar_accion(600, lambda: self.tono_buzzer(.25))
        self.programar_accion(900, lambda: GPIO.output(24, GPIO.LOW))
        self.mostrar_standby()

    def leer_botones(self):
        if self._cerrando:
            return
        try:
            ahora = time.monotonic()
            self.actualizar_presencia(ahora)
            bajos = {pin for pin in self._pines_botones if GPIO.input(pin) == GPIO.LOW}
            pin = self.detectar_pulsacion(bajos, ahora)
            # Este plazo empieza con la primera pulsación aceptada y se renueva
            # con cada dígito; es independiente de los 4 s de presencia retenida.
            vencio = (self._captura_metodo == "botones" and not self._en_resultado
                      and ahora - self._ultima_pulsacion >= 4)
            if vencio:
                # Regla conservada del programa físico: una clave de 4 o 5
                # dígitos se envía al vencer el plazo; con 6 se envía de inmediato.
                # Un identificador incompleto o clave de menos de 4 se descarta.
                if self._captura_fase == "clave" and len(self._captura_clave) >= 4:
                    self.validar_botones()
                else:
                    self.cancelar_captura_fisica()
            elif pin is not None:
                if self._en_resultado:
                    print("[IGNORADO] Mostrando resultado.", flush=True)
                elif self._captura_metodo == "interfaz_grafica":
                    print("[IGNORADO] La pantalla está atendiendo este intento.", flush=True)
                elif self._captura_metodo is None and not self.pir_activo:
                    print("[IGNORADO] Sin presencia habilitada. Espere la estabilización y acérquese al PIR.", flush=True)
                else:
                    if self._captura_metodo is None:
                        self._captura_metodo = "botones"
                        self._captura_fase = "identificador"
                        self._captura_id = self._captura_clave = ""
                        print("[MÉTODO] Botones. Capture 4 dígitos de identificador.", flush=True)
                    self.agregar_boton(self._pines_botones[pin], ahora)
        except Exception as error:
            print("Error en hardware:", error)
            if messagebox is not None and not isinstance(self, ModoBotones):
                messagebox.showerror("Error de hardware", str(error))
            self.on_closing()
            return
        # Sondeo aproximado cada 20 ms; la consulta síncrona a MySQL puede
        # retrasarlo durante la validación, cuando ya no se aceptan más dígitos.
        self._hardware_after = self.root.after(20, self.leer_botones)

    def agregar_boton(self, valor, ahora):
        print(f"[ACEPTADO] Pulsación; campo: {self._captura_fase}", flush=True)
        self._ultima_pulsacion = ahora
        self.tono_buzzer(.04)
        if self._captura_fase == "identificador":
            self._captura_id += valor
            print(f"[IDENTIFICADOR] {self._captura_id} ({len(self._captura_id)}/4)", flush=True)
            # Cambiar de fase después de guardar el cuarto dígito: ese mismo
            # botón NO se reutiliza como primer dígito de la contraseña.
            if len(self._captura_id) == 4:
                self._captura_fase = "clave"
                print("[CLAVE] Identificador completo. La SIGUIENTE pulsación inicia la clave.", flush=True)
        else:
            self._captura_clave += valor
            print("Dígitos de clave capturados:", len(self._captura_clave))
            if len(self._captura_clave) == 6:
                self.validar_botones()

    def validar_botones(self):
        # Aquí no hay un rol elegido en pantalla. La función original de DB
        # valida las credenciales y el permiso de apertura y registra "botones".
        self.identificador = self._captura_id
        try:
            resultado = (validar_acceso(self._captura_id, self._captura_clave, "botones")
                         if validar_acceso is not None else "error_sistema")
        except Exception as error:
            print("Error al validar botones:", error)
            resultado = "error_sistema"
        self._captura_id = self._captura_clave = ""
        self.mostrar_resultado(resultado)

    # ============ 9. LIBERACIÓN DE HARDWARE Y ELEMENTOS DE PANTALLA ============
    def cerrar_hardware(self):
        # Puede llamarse desde el cierre de ventana y desde finally: limpiar
        # una sola vez evita liberar dos veces los mismos recursos.
        if getattr(self, "_hardware_cerrado", False):
            return
        self._hardware_cerrado = True
        if self._servo_chip is not None:
            if getattr(self, "_servo_reclamado", False):
                try:
                    lgpio.tx_servo(self._servo_chip, 26, 1500)
                    time.sleep(.25)
                    lgpio.tx_servo(self._servo_chip, 26, 0)
                    lgpio.gpio_free(self._servo_chip, 26)
                finally:
                    self._servo_reclamado = False
            lgpio.gpiochip_close(self._servo_chip)
            self._servo_chip = None
        if self._gpio_iniciado:
            GPIO.cleanup()
            self._gpio_iniciado = False

    def limpiar_frame(self):
        """Limpia el contenido del frame principal"""
        if self._pir_after is not None:
            self.root.after_cancel(self._pir_after)
            self._pir_after = None
        # Cancelar la lectura antes de destruir sus elementos evita el error
        # "invalid command name" al intentar actualizar un canvas eliminado.
        # Desvincular Espacio para que no cambie de pantalla durante el login.
        self.root.unbind("<space>")

        for widget in self.main_frame.winfo_children():
            widget.destroy()


# ============ 10. TEMPORIZADORES SIN ESCRITORIO ============
# Sustituye solo after/after_cancel/mainloop: no simula una interfaz ni GPIO.
class TemporizadorFisico:
    """Temporizadores sin Tk: el modo físico no necesita un escritorio."""
    def __init__(self):
        self._cola = []
        self._ids = itertools.count()
        self._pendientes = set()
        self.activo = True

    def after(self, ms, funcion):
        token = next(self._ids) + 1
        self._pendientes.add(token)
        heapq.heappush(self._cola, (time.monotonic() + ms / 1000, token, funcion))
        return token

    def after_cancel(self, token):
        # Cancelación diferida: el elemento queda en la cola, pero mainloop
        # lo omite cuando llega su turno si ya no está en _pendientes.
        self._pendientes.discard(token)

    def destroy(self):
        self.activo = False
        self._cola.clear()
        self._pendientes.clear()

    def mainloop(self):
        while self.activo:
            ahora = time.monotonic()
            while self._cola and self._cola[0][0] <= ahora and self.activo:
                _, token, funcion = heapq.heappop(self._cola)
                if token in self._pendientes:
                    self._pendientes.remove(token)
                    funcion()
                ahora = time.monotonic()
            time.sleep(.005)


# ============ 11. MODO FÍSICO SIN INTERFAZ (SSH) ============
# Hereda la lógica de hardware y captura; sustituye las pantallas por mensajes.
class ModoBotones(InterfazControlAcceso):
    """Reutiliza la captura y el hardware sin construir ninguna ventana."""
    def __init__(self, root):
        self.root = root
        self.preparar_estado()
        self.crear_lock()
        self._gpio_iniciado = True
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIR_PIN, GPIO.IN)
        self.inicializar_hardware()
        self.identificador = ""
        self.pir_activo = False
        self.mostrar_standby()
        self.leer_botones()

    def anunciar_sistema_listo(self):
        self.tono_buzzer(.15)
        print("[LISTO] Acceso físico habilitado.", flush=True)

    def mostrar_standby(self):
        if self._en_resultado:
            lgpio.tx_servo(self._servo_chip, 26, 1500)
        self._en_resultado = False
        self._captura_metodo = None
        self._captura_id = self._captura_clave = ""
        self._captura_fase = "identificador"
        self._hardware_armado = False
        self._presencia_hasta = 0.0
        self._esperar_liberacion = True
        self.pir_activo = False
        print("[SOLO BOTONES] Esperando sensor. Identificador: 4 pulsaciones; clave: 4 a 6.", flush=True)

    def mostrar_resultado(self, resultado, accionar=True):
        self._en_resultado = True
        mensajes = {
            "autorizado": "ACCESO AUTORIZADO",
            "sin_permiso": "ACCESO DENEGADO: usuario sin permiso",
            "no_reconocido": "ACCESO RECHAZADO: datos incorrectos",
            "error_sistema": "ERROR DEL SISTEMA: no se pudo validar",
        }
        print(mensajes.get(resultado, mensajes["error_sistema"]), flush=True)
        if accionar:
            self.respuesta_hardware(resultado)
        self.programar_accion(4000, self.mostrar_standby)


# ============ 12. ARRANQUE, RESPALDO AUTOMÁTICO Y SALIDA ============
def liberar_aplicacion(app, root):
    try:
        if app is not None and hasattr(app, "_servo_chip"):
            app.cerrar_hardware()
    finally:
        if app is not None and hasattr(app, "_lock_handle"):
            app.limpiar_lock()
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass


def ejecutar_solo_botones():
    print("[MODO] Acceso físico activo. Ctrl+C para cerrar.", flush=True)
    root = TemporizadorFisico()
    app = ModoBotones.__new__(ModoBotones)
    try:
        app.__init__(root)
        root.mainloop()
    except KeyboardInterrupt:
        print("Programa detenido por el usuario.", flush=True)
    finally:
        liberar_aplicacion(app, root)


def ejecutar_interfaz():
    """Devuelve True solo si debe continuar sin pantalla."""
    if tk is None:
        print("[INTERFAZ] Tkinter no está disponible. Se usará el modo físico.", flush=True)
        return True
    root = None
    app = None
    fallback = False
    try:
        root = tk.Tk()
        root.withdraw()  # Mostrar solo después de estabilización y reposo del PIR.
        # Los errores recuperables de callbacks terminan esta sesión gráfica.
        # Se libera el hardware y se inicia una sesión física nueva: no se
        # conserva un intento a medias. Esto no recupera un proceso terminado
        # ni un bloqueo total del sistema o del servidor gráfico.
        def error_interfaz(tipo, error, traza):
            nonlocal fallback
            print("[INTERFAZ] Falló una operación de pantalla:", error, flush=True)
            print("[MODO] Se cancelará el intento actual y se reiniciará en modo físico.", flush=True)
            fallback = True
            root.quit()
        root.report_callback_exception = error_interfaz
        app = InterfazControlAcceso.__new__(InterfazControlAcceso)
        app.__init__(root)
        root.mainloop()
    except tk.TclError as error:
        print("[INTERFAZ] No se pudo usar la pantalla:", error, flush=True)
        fallback = True
    except KeyboardInterrupt:
        print("Programa detenido por el usuario.", flush=True)
    finally:
        liberar_aplicacion(app, root)
    return fallback


def main():
    parser = argparse.ArgumentParser(description="Acceso por interfaz y botones, con respaldo sin pantalla.")
    parser.add_argument("--solo-botones", action="store_true",
                        help="No abrir interfaz; usar sensor, botones, MySQL, servo, LEDs y buzzer.")
    args = parser.parse_args()
    # Con --solo-botones ni siquiera se intenta abrir Tk. Sin esa opción,
    # ejecutar_interfaz devuelve True si hace falta el respaldo sin pantalla.
    # Cerrar la ventana normalmente NO inicia el modo físico.
    if args.solo_botones or ejecutar_interfaz():
        ejecutar_solo_botones()


if __name__ == "__main__":
    main()
