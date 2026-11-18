import base64
import hashlib
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from api.app import crear_api


class PruebaSesionFacial(unittest.TestCase):
    def setUp(self):
        self.ahora = 100
        self.verificar = Mock(return_value=7)
        self.cliente = TestClient(
            crear_api(verificar_rostro=self.verificar, reloj=lambda: self.ahora)
        )
        self.addCleanup(self.cliente.close)
        self.frontal = b"JPEG frontal"
        self.inclinada = b"JPEG inclinado"
        parche = patch(
            "api.sesion_facial.autenticacion.iniciar_sesion_usuario_verificado",
            return_value={"token": "token-prueba", "expira": datetime(2030, 1, 1, tzinfo=timezone.utc)},
        )
        self.emitir = parche.start()
        self.addCleanup(parche.stop)

    def pedir_reto(self):
        return self.cliente.post(
            "/sessions/face/challenge",
            json={"front_sha256": hashlib.sha256(self.frontal).hexdigest()},
        )

    def verificar_reto(self, reto, frontal=None, client=None):
        cliente = self.cliente if client is None else client
        return cliente.post(
            "/sessions/face",
            json={
                "challenge_id": reto["challenge_id"],
                "front_image": base64.b64encode(
                    self.frontal if frontal is None else frontal
                ).decode(),
                "tilted_image": base64.b64encode(self.inclinada).decode(),
            },
        )

    def test_sesion_estandar_y_reto_de_un_solo_uso(self):
        reto = self.pedir_reto().json()
        respuesta = self.verificar_reto(reto)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["token"], "token-prueba")
        self.assertEqual(self.verificar_reto(reto).status_code, 401)
        self.verificar.assert_called_once_with(self.frontal, self.inclinada, reto["direction"])
        self.emitir.assert_called_once_with(7)

    def test_no_emite_si_verificador_rechaza_o_la_cuenta_esta_inactiva(self):
        self.verificar.return_value = None
        self.assertEqual(self.verificar_reto(self.pedir_reto().json()).status_code, 401)
        self.emitir.assert_not_called()

        self.verificar.return_value = 7
        self.emitir.return_value = None
        self.assertEqual(self.verificar_reto(self.pedir_reto().json()).status_code, 401)
        self.emitir.assert_called_once_with(7)

    def test_rechaza_reto_vencido_o_con_captura_frontal_distinta(self):
        self.assertEqual(
            self.verificar_reto(self.pedir_reto().json(), frontal=b"imagen distinta").status_code,
            401,
        )
        reto = self.pedir_reto().json()
        self.ahora += 45
        self.assertEqual(self.verificar_reto(reto).status_code, 401)
        self.verificar.assert_not_called()
        self.emitir.assert_not_called()

    def test_rechaza_otro_cliente_sin_consumir_el_reto(self):
        reto = self.pedir_reto().json()
        with TestClient(self.cliente.app, client=("otro-cliente", 50000)) as otro:
            self.assertEqual(self.verificar_reto(reto, client=otro).status_code, 401)
        self.assertEqual(self.verificar_reto(reto).status_code, 200)
        self.verificar.assert_called_once()

    def test_limites_por_direccion_y_tamano(self):
        for _ in range(5):
            self.assertEqual(self.pedir_reto().status_code, 200)
        respuesta = self.pedir_reto()
        self.assertEqual(respuesta.status_code, 429)
        self.assertEqual(respuesta.headers["Retry-After"], "60")
        self.assertEqual(
            self.cliente.post("/sessions/face", content=b" " * 710000).status_code,
            413,
        )
        self.verificar.assert_not_called()

    def test_servicio_sin_modelo_no_ofrece_retos_ni_sesiones(self):
        with TestClient(crear_api()) as cliente:
            self.assertEqual(cliente.post("/sessions/face/challenge").status_code, 503)
            self.assertEqual(cliente.post("/sessions/face").status_code, 503)
        self.emitir.assert_not_called()
