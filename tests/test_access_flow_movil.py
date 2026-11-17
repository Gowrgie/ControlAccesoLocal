import sys
import unittest
from time import monotonic
from unittest.mock import Mock, patch
from uuid import uuid4


class PruebaFlujoMovil(unittest.TestCase):
    def test_espera_su_turno_y_completa_al_volver_a_reposo(self):
        with patch.dict(sys.modules, {"hardware": Mock()}):
            from access_flow import ControlAcceso

            control = ControlAcceso()
            control.root = Mock()
            control.preparar_estado()
            control.hardware.pir.presencia_para_api.side_effect = (
                lambda ahora: control.hardware.pir.activo
            )
            control.hardware.botones.detectar_pulsacion.return_value = None

            def mostrar_resultado(resultado, accionar=True):
                control._en_resultado = True
                if accionar:
                    control.hardware.respuesta_hardware(resultado)

            control.mostrar_resultado = mostrar_resultado
            request_id = str(uuid4())
            control.despachador.enviar(request_id, "sesion-1", 7)

            with patch(
                "access_flow.validar_acceso_movil", return_value="autorizado"
            ) as validar:
                control.hardware.pir.activo = False
                control.leer_botones()
                validar.assert_not_called()

                control.hardware.pir.activo = True
                for metodo in ("botones", "interfaz_grafica", "facial"):
                    with self.subTest(metodo=metodo):
                        control._captura_metodo = metodo
                        control._ultima_pulsacion = monotonic()
                        control.leer_botones()

                        self.assertFalse(control._cerrando)
                        validar.assert_not_called()
                        control.hardware.respuesta_hardware.assert_not_called()

                        estado = control.despachador.consultar(request_id, "sesion-1")
                        self.assertEqual(estado["state"], "busy")

                control.reiniciar_estado_espera()
                control.hardware.pir.activo = True
                control.leer_botones()
                validar.assert_called_once_with(7)
                control.hardware.respuesta_hardware.assert_called_once_with("autorizado")

                estado = control.despachador.consultar(request_id, "sesion-1")
                self.assertEqual(estado["state"], "pending")

                control.reiniciar_estado_espera()
                control.hardware.servo_reposo.assert_called_once_with()
                estado = control.despachador.consultar(request_id, "sesion-1")
                self.assertEqual(estado["state"], "complete")
                self.assertEqual(estado["result"], "autorizado")