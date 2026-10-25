"""Entry point of the access control system (GUI and buttons in one program).

Flow: stabilize PIR -> wait for presence -> capture by one method
-> query MySQL -> indicate result and move servo -> back to rest.

Run from the src/ folder:
    python Main_code.py                  GUI, with automatic fallback to buttons
    python Main_code.py --solo-botones   physical only, also works over SSH

Modules:
    hardware.py       GPIO, PIR, buttons, LEDs, buzzer, servo, process lock
    audio.py          speaker tones
    access_logic.py   authorization decision against the database
    access_flow.py    capture/validation flow shared by both modes
    gui.py            Tkinter screens
    headless_mode.py  physical mode without a desktop
    camera.py         provided by the hardware team: camara_disponible() -> bool

Without a working camera the facial method cannot be used, so the system
starts in button-only mode (the same mode as --solo-botones).

Extra dependencies: lgpio and scripts_db/db_conexion.py. Audio tones need
speaker-test; the GPIO buzzer is independent. On Ubuntu, tkinter may need
the python3-tk package.
"""
import argparse

from gui import InterfazControlAcceso, tk
from headless_mode import ModoBotones, TemporizadorFisico

# camera.py is written by the hardware team. camara_disponible() must return
# True when frames can be read, and must release the camera before returning.
try:
    from camera import camara_disponible
except ModuleNotFoundError as error:
    if error.name == "camera":
        camara_disponible = None  # no camera module in this build: facial recognition is not installed
    else:
        camara_disponible = lambda: False  # the module exists but a library it needs is missing
except ImportError:
    camara_disponible = lambda: False


def liberar_aplicacion(app, root):
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
    """Returns True only if it must continue without a screen."""
    if tk is None:
        print("[INTERFAZ] Tkinter no está disponible. Se usará el modo físico.", flush=True)
        return True
    root = None
    app = None
    fallback = False
    try:
        root = tk.Tk()
        root.withdraw()  # Shown only after PIR stabilization and rest.

        # Recoverable callback errors end this graphical session. The hardware
        # is released and a new physical session starts: a half-done attempt
        # is not kept. This does not recover a terminated process or a total
        # freeze of the system or the graphical server.
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


def camara_no_disponible():
    """True only when the facial method cannot be used: the camera module says
    the camera does not work, fails while checking, or could not be loaded."""
    if camara_disponible is None:
        return False  # no camera module in this build: there is nothing to check
    try:
        return not camara_disponible()
    except Exception as error:
        print("[CAMARA] Error al comprobar la camara:", error, flush=True)
        return True


def main():
    parser = argparse.ArgumentParser(description="Acceso por interfaz y botones, con respaldo sin pantalla.")
    parser.add_argument("--solo-botones", action="store_true",
                        help="No abrir interfaz; usar sensor, botones, MySQL, servo, LEDs y buzzer.")
    args = parser.parse_args()
    # Without a working camera the facial method is not available: start in
    # button-only mode, the same one --solo-botones asks for.
    if camara_no_disponible():
        print("[CAMARA] No disponible. El sistema inicia solo con botones.", flush=True)
        ejecutar_solo_botones()
    # With --solo-botones Tk is not even tried. Without it, ejecutar_interfaz
    # returns True if the screenless fallback is needed. Closing the window
    # normally does NOT start physical mode.
    elif args.solo_botones or ejecutar_interfaz():
        ejecutar_solo_botones()


if __name__ == "__main__":
    main()