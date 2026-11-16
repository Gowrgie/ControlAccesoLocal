"""Entry point of the access control system (GUI and buttons in one program).

Flow: stabilize PIR -> wait for presence -> capture by one method
-> query MySQL -> indicate result and move servo -> back to rest.

Run from the src/ folder:
    python Main_code.py                  GUI and physical buttons
    python Main_code.py --solo-botones   physical buttons only; also works over SSH

If the camera is unavailable, the graphical interface still opens.
The GUI handles the facial recognition failure and leaves the other
access methods available.

Modules:
    hardware.py       GPIO, PIR, buttons, LEDs, buzzer, servo, process lock
    audio.py          speaker tones
    access_logic.py   authorization decision against the database
    access_flow.py    capture/validation flow shared by both modes
    gui.py            Tkinter screens
    headless_mode.py  physical mode without a desktop

Extra dependencies: lgpio and scripts_db/db_conexion.py. Audio tones need
speaker-test; the GPIO buzzer is independent. On Ubuntu, tkinter may need
the python3-tk package.
"""

import argparse

from gui import InterfazControlAcceso, tk
from headless_mode import ModoBotones, TemporizadorFisico

def iniciar_api_movil(app, config_api):
    if config_api is None or app._cerrando:
        return None

    try:
        from api.server import ServidorApiMovil

        servidor = ServidorApiMovil(app, **config_api)
        servidor.iniciar()
        return servidor
    except (ImportError, OSError, ValueError) as error:
        print(f"[API MÓVIL] No se pudo iniciar HTTPS: {error}", flush=True)
        return None


def liberar_aplicacion(app, root, servidor_api=None):
    """Release hardware resources and destroy the application window."""
    if servidor_api is not None:
        servidor_api.cerrar()

    try:
        if app is not None and hasattr(app, "hardware"):
            app.hardware.cerrar_hardware()
    finally:
        if app is not None and hasattr(app, "hardware"):
            app.hardware.limpiar_lock()

        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass


def ejecutar_solo_botones(config_api=None):
    """Run the physical button mode without the graphical interface."""
    print("[MODO] Acceso físico activo. Ctrl+C para cerrar.", flush=True)

    root = TemporizadorFisico()
    app = ModoBotones.__new__(ModoBotones)
    servidor_api = None

    try:
        app.__init__(root)
        servidor_api = iniciar_api_movil(app, config_api)
        root.mainloop()
    except KeyboardInterrupt:
        print("Programa detenido por el usuario.", flush=True)
    finally:
        liberar_aplicacion(app, root, servidor_api)


def ejecutar_interfaz(config_api=None):
    """Run the GUI and return True if physical fallback is needed."""
    if tk is None:
        print(
            "[INTERFAZ] Tkinter no está disponible. "
            "Se usará el modo físico.",
            flush=True,
        )
        return True

    root = None
    app = None
    servidor_api = None
    fallback = False

    try:
        root = tk.Tk()
        root.withdraw()  # Shown only after PIR stabilization and rest.

        def error_interfaz(tipo, error, traza):
            nonlocal fallback

            print(
                "[INTERFAZ] Falló una operación de pantalla:",
                error,
                flush=True,
            )
            print(
                "[MODO] Se cancelará el intento actual y se reiniciará "
                "en modo físico.",
                flush=True,
            )
            fallback = True
            root.quit()

        root.report_callback_exception = error_interfaz

        app = InterfazControlAcceso.__new__(InterfazControlAcceso)
        app.__init__(root)
        servidor_api = iniciar_api_movil(app, config_api)
        root.mainloop()

    except tk.TclError as error:
        print("[INTERFAZ] No se pudo usar la pantalla:", error, flush=True)
        fallback = True
    except KeyboardInterrupt:
        print("Programa detenido por el usuario.", flush=True)
    finally:
        liberar_aplicacion(app, root, servidor_api)

    return fallback


def main():
    parser = argparse.ArgumentParser(
        description="Control de acceso local para Raspberry Pi"
    )
    parser.add_argument(
        "--solo-botones",
        action="store_true",
        help="Ejecutar el controlador en modo físico sin interfaz gráfica",
    )
    parser.add_argument(
        "--api-host",
        help="Dirección IP local donde escuchará el servidor HTTPS",
    )
    parser.add_argument("--api-cert", help="Ruta al certificado HTTPS en PEM")
    parser.add_argument("--api-key", help="Ruta a la clave privada HTTPS en PEM")

    args = parser.parse_args()

    opciones_api = (args.api_host, args.api_cert, args.api_key)
    if any(opciones_api) and not all(opciones_api):
        parser.error("--api-host, --api-cert y --api-key deben usarse juntos")

    config_api = None
    if all(opciones_api):
        config_api = {
            "host": args.api_host,
            "certificado": args.api_cert,
            "clave_privada": args.api_key,
        }

    if args.solo_botones:
        ejecutar_solo_botones(config_api)
    elif ejecutar_interfaz(config_api):
        ejecutar_solo_botones(config_api)


if __name__ == "__main__":
    main()