import unittest
from unittest.mock import Mock, patch

from Main_code import iniciar_api_movil


class PruebaApiMovilNoBloqueante(unittest.TestCase):
    def test_fallo_al_iniciar_la_api_no_detiene_la_app(self):
        app = Mock()
        app._cerrando = False
        config_api = {
            "host": "127.0.0.1",
            "certificado": "no-existe.pem",
            "clave_privada": "no-existe.pem",
        }

        with patch(
            "api.server.ServidorApiMovil",
            side_effect=ValueError("HTTPS requiere un certificado y una clave privada"),
        ):
            servidor = iniciar_api_movil(app, config_api)

        self.assertIsNone(servidor)

    def test_sin_config_no_intenta_iniciar_la_api(self):
        app = Mock()
        app._cerrando = False
        self.assertIsNone(iniciar_api_movil(app, None))