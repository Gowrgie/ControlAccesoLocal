"""Audio module: tones and spoken messages played through the system speakers.

Uses the Ubuntu audio output (alsa-utils: speaker-test for tones, aplay for
messages). It is independent from the GPIO buzzer, which belongs to
hardware.py. Everything is local: no internet or cloud service is needed.

Tones (if the audio output is not available, nothing is played and no error
is raised):
    reproducir_tono(frecuencia=1000, duracion=0.5)
    reproducir_sonido_exito()    -> access granted
    reproducir_sonido_error()    -> access denied
    reproducir_sonido_alerta()   -> system error

Spoken messages, recorded as WAV files in the audio_messages/ folder next to
this module (all Spanish):
    reproducir_mensaje_autorizado()   authorized.wav  "Acceso correcto"
    reproducir_mensaje_denegado()     denied.wav      "Acceso denegado"
    reproducir_mensaje_error()        error.wav       "Error del sistema"
    reproducir_mensaje(nombre)        nombre: "autorizado", "denegado" or "error"
    reproducir_mensaje_resultado(resultado)
        resultado: any of the four results of access_logic.py

A message never blocks the caller and a new message replaces the one that is
still playing. Each function returns True when the message started playing,
or False when the tone of the same situation was played instead (the WAV
file is missing or aplay is not installed).
"""
import os
import subprocess
import time


def reproducir_tono(frecuencia=1000, duracion=0.5):
    """Play a sine tone using speaker-test."""
    try:
        os.system(f'(speaker-test -t sine -f {frecuencia} -l 1 & sleep {duracion}; killall speaker-test) 2>/dev/null &')
    except:  # kept exactly as in the original code
        pass


def reproducir_sonido_exito():
    """Access granted: two ascending tones."""
    reproducir_tono(1000, 0.3)
    time.sleep(0.1)
    reproducir_tono(1200, 0.3)


def reproducir_sonido_error():
    """Access denied: two descending tones."""
    reproducir_tono(600, 0.2)
    time.sleep(0.1)
    reproducir_tono(400, 0.2)


def reproducir_sonido_alerta():
    """System alert: two tones."""
    reproducir_tono(800, 0.25)
    time.sleep(0.15)
    reproducir_tono(600, 0.25)


# ============ spoken messages ============
CARPETA_MENSAJES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_messages")
REPRODUCTOR = "aplay"  # alsa-utils, the same package that provides speaker-test

# message name -> (WAV file, tone played instead when the message cannot be played)
MENSAJES = {
    "autorizado": ("authorized.wav", reproducir_sonido_exito),
    "denegado": ("denied.wav", reproducir_sonido_error),
    "error": ("error.wav", reproducir_sonido_alerta),
}

# result of access_logic.py -> message
MENSAJE_POR_RESULTADO = {
    "autorizado": "autorizado",
    "sin_permiso": "denegado",
    "no_reconocido": "denegado",
    "error_sistema": "error",
}

_reproduccion_actual = None


def reproducir_mensaje(nombre):
    """Plays a recorded message without blocking the caller."""
    global _reproduccion_actual
    if nombre not in MENSAJES:
        raise ValueError(f"Mensaje de audio desconocido: {nombre}")
    archivo, sonido_respaldo = MENSAJES[nombre]
    ruta = os.path.join(CARPETA_MENSAJES, archivo)

    # A new message replaces the one still playing, so they never overlap.
    if _reproduccion_actual is not None and _reproduccion_actual.poll() is None:
        _reproduccion_actual.terminate()
    _reproduccion_actual = None

    if os.path.isfile(ruta):
        try:
            _reproduccion_actual = subprocess.Popen(
                [REPRODUCTOR, "-q", ruta],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return True
        except OSError:
            pass  # aplay is not installed
    sonido_respaldo()
    return False


def reproducir_mensaje_autorizado():
    """Access granted: "Acceso correcto"."""
    return reproducir_mensaje("autorizado")


def reproducir_mensaje_denegado():
    """Access denied: "Acceso denegado"."""
    return reproducir_mensaje("denegado")


def reproducir_mensaje_error():
    """System error: "Error del sistema"."""
    return reproducir_mensaje("error")


def reproducir_mensaje_resultado(resultado):
    """Plays the message that matches a result of access_logic.py.
    An unknown value is treated as denied, like the result screen does."""
    return reproducir_mensaje(MENSAJE_POR_RESULTADO.get(resultado, "denegado"))