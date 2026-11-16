import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from api.app import crear_api


class PruebaApiPresencia(unittest.TestCase):
    def setUp(self):
        self.obtener_presencia = Mock()
        self.cliente = TestClient(
            crear_api(obtener_presencia=self.obtener_presencia)
        )
        self.addCleanup(self.cliente.close)
        self.encabezados = {"Authorization": "Bearer token-prueba"}

    def test_devuelve_el_estado_del_pir(self):
        with patch("api.app.autenticacion.validar_sesion", return_value=7):
            for presente in (True, False):
                with self.subTest(presente=presente):
                    self.obtener_presencia.return_value = presente
                    respuesta = self.cliente.get(
                        "/presence", headers=self.encabezados
                    )

                    self.assertEqual(respuesta.status_code, 200)
                    self.assertEqual(respuesta.json(), {"present": presente})

    def test_sensor_no_disponible_devuelve_503(self):
        self.obtener_presencia.return_value = None

        with patch("api.app.autenticacion.validar_sesion", return_value=7):
            respuesta = self.cliente.get("/presence", headers=self.encabezados)

        self.assertEqual(respuesta.status_code, 503)

    def test_token_invalido_devuelve_401_sin_consultar_el_pir(self):
        with patch(
            "api.app.autenticacion.validar_sesion", return_value=None
        ) as validar_sesion:
            respuesta = self.cliente.get("/presence", headers=self.encabezados)

        validar_sesion.assert_called_once_with("token-prueba")
        self.assertEqual(respuesta.status_code, 401)
        self.obtener_presencia.assert_not_called()