import sys
import unittest
from unittest.mock import Mock, patch


class PruebaAlternativasPIR(unittest.TestCase):
    def setUp(self):
        modulos = patch.dict(sys.modules, {"hardware": Mock(VENTANA_PRESENCIA=4.0)})
        modulos.start()
        self.addCleanup(modulos.stop)

        import gui

        self.control = gui.InterfazControlAcceso.__new__(gui.InterfazControlAcceso)
        self.control.root = Mock()
        self.control.preparar_estado()
        self.control.timeout_pir = 30
        self.control.main_frame = Mock()
        self.control.limpiar_frame = Mock()
        self.control.mostrar_standby = Mock(
            side_effect=self.control.reiniciar_estado_espera
        )
        self.control.hardware.pir.presencia_para_api.return_value = True
        with patch.object(gui, "ttk"), patch.object(gui.time, "monotonic", return_value=100):
            self.control.mostrar_alternativas_facial("Elige otro método")

    def test_vuelve_a_espera_al_vencer_la_presencia(self):
        self.control.actualizar_presencia(101)
        self.control.mostrar_standby.assert_not_called()

        self.control.hardware.pir.presencia_para_api.return_value = False
        self.control.actualizar_presencia(106)

        self.control.mostrar_standby.assert_called_once_with()
        self.assertIsNone(self.control._captura_metodo)
        self.control.hardware.respuesta_hardware.assert_not_called()

    def test_da_tiempo_para_elegir_aunque_la_presencia_ya_haya_vencido(self):
        self.control.hardware.pir.presencia_para_api.return_value = False
        self.control.actualizar_presencia(100.01)
        self.control.actualizar_presencia(103.99)
        self.control.mostrar_standby.assert_not_called()

        self.control.actualizar_presencia(104)

        self.control.mostrar_standby.assert_called_once_with()

    def test_vuelve_a_espera_por_inactividad_con_presencia_activa(self):
        self.control.actualizar_presencia(129.9)
        self.control.mostrar_standby.assert_not_called()

        self.control.actualizar_presencia(130)

        self.control.mostrar_standby.assert_called_once_with()
        self.assertIsNone(self.control._captura_metodo)

    def test_el_plazo_no_interrumpe_un_metodo_ya_elegido(self):
        self.control.mostrar_seleccion_rol = Mock()
        self.control.seleccionar_interfaz_alternativa()
        self.control.hardware.pir.presencia_para_api.return_value = False

        self.control.actualizar_presencia(131)

        self.control.mostrar_seleccion_rol.assert_called_once_with()
        self.control.mostrar_standby.assert_not_called()
        self.assertEqual(self.control._captura_metodo, "interfaz_grafica")
