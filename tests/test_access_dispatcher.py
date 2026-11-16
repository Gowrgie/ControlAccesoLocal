import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

from access_dispatcher import DespachadorAcceso


class PruebaDespachador(unittest.TestCase):
    def test_uuid_repetido_en_paralelo_solo_se_encola_una_vez(self):
        dispatcher = DespachadorAcceso()
        request_id = str(uuid4())
        barrera = Barrier(4, timeout=5)

        def enviar(_):
            barrera.wait()
            return dispatcher.enviar(request_id, "sesion-1", 7)

        with ThreadPoolExecutor(max_workers=4) as ejecutor:
            resultados = list(ejecutor.map(enviar, range(4)))

        self.assertEqual(sum(resultados), 1)
        activa = dispatcher.tomar(controlador_ocupado=False)
        self.assertEqual(activa.request_id, request_id)
        dispatcher.completar(request_id, "autorizado")
        self.assertIsNone(dispatcher.tomar(controlador_ocupado=False))

    def test_vencimiento_solo_afecta_la_cola(self):
        ahora = 0
        dispatcher = DespachadorAcceso(reloj=lambda: ahora)
        primera, segunda = str(uuid4()), str(uuid4())
        dispatcher.enviar(primera, "sesion-1", 7)
        dispatcher.enviar(segunda, "sesion-1", 7)

        ahora = 9
        activa = dispatcher.tomar(controlador_ocupado=False)
        self.assertEqual(activa.request_id, primera)

        ahora = 10
        self.assertEqual(dispatcher.consultar(primera, "sesion-1")["state"], "pending")
        self.assertEqual(dispatcher.consultar(segunda, "sesion-1")["state"], "expired")

        dispatcher.completar(primera, "autorizado")
        self.assertFalse(dispatcher.enviar(segunda, "sesion-1", 7))
        self.assertIsNone(dispatcher.tomar(controlador_ocupado=False))

    def test_otra_sesion_no_puede_consultar_ni_reutilizar_el_uuid(self):
        dispatcher = DespachadorAcceso()
        request_id = str(uuid4())
        dispatcher.enviar(request_id, "sesion-1", 7)

        with self.assertRaises(PermissionError):
            dispatcher.consultar(request_id, "sesion-2")

        with self.assertRaises(PermissionError):
            dispatcher.enviar(request_id, "sesion-2", 8)