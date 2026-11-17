import importlib
import sys
import unittest
from unittest.mock import Mock, patch


class PruebaApiMovilNoBloqueante(unittest.TestCase):
    def setUp(self):
        self.servidor_api = Mock()
        hardware = Mock()
        self.control_hardware = hardware.ControlHardware.return_value
        self.control_hardware.botones.detectar_pulsacion.return_value = None
        self.control_hardware.pir.presencia_para_api.return_value = False

        modulos = {
            "hardware": hardware,
            "api.server": Mock(ServidorApiMovil=self.servidor_api),
        }
        parche = patch.dict(sys.modules, modulos)
        parche.start()
        self.addCleanup(parche.stop)
        self.main_code = importlib.import_module("Main_code")

    def test_fallo_al_iniciar_la_api_no_detiene_el_bucle_de_botones(self):
        raiz = Mock()
        self.servidor_api.side_effect = ValueError("Certificado HTTPS inválido")
        config_api = {
            "host": "127.0.0.1",
            "certificado": "no-existe.pem",
            "clave_privada": "no-existe.pem",
        }

        def verificar_bucle_activo():
            self.servidor_api.assert_called_once()
            self.control_hardware.cerrar_hardware.assert_not_called()

        raiz.mainloop.side_effect = verificar_bucle_activo
        with patch.object(self.main_code, "TemporizadorFisico", return_value=raiz):
            self.main_code.ejecutar_solo_botones(config_api)

        raiz.mainloop.assert_called_once_with()
        self.control_hardware.cerrar_hardware.assert_called_once_with()

    def test_sin_config_no_intenta_iniciar_la_api(self):
        app = Mock(_cerrando=False)

        self.assertIsNone(self.main_code.iniciar_api_movil(app, None))
        self.servidor_api.assert_not_called()