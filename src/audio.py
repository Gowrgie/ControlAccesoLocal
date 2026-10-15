"""Audio module: tones played through the system speakers.

Uses the Ubuntu audio output (speaker-test). It is independent from the GPIO
buzzer, which belongs to hardware.py. If speaker-test or the audio output is
not available, nothing is played and no error is raised.

Public interface:
    reproducir_tono(frecuencia=1000, duracion=0.5)
    reproducir_sonido_exito()    -> access granted
    reproducir_sonido_error()    -> access denied
    reproducir_sonido_alerta()   -> system error
"""
import os
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