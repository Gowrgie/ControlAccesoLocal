import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from access_dispatcher import DespachadorAcceso
from api.app import crear_api


class PruebaApiSolicitudes(unittest.TestCase):
    def setUp(self):
        self.despachador = DespachadorAcceso()
        self.presencia = Mock(return_value=True)
        self.cliente = TestClient(
            crear_api(
                obtener_presencia=self.presencia,
                despachador=self.despachador,
            )
        )
        self.addCleanup(self.cliente.close)

        autenticacion = patch(
            "api.app.autenticacion.validar_sesion", return_value=7
        )
        autenticacion.start()
        self.addCleanup(autenticacion.stop)

        self.request_id = str(uuid4())

    def enviar(self, token="token-prueba"):
        return self.cliente.post(
            "/access-requests",
            json={"request_id": self.request_id},
            headers={"Authorization": f"Bearer {token}"},
        )

    def test_solicitud_nueva_se_encola(self):
        respuesta = self.enviar()

        self.assertEqual(respuesta.status_code, 202)
        self.assertEqual(
            respuesta.json(),
            {"request_id": self.request_id, "state": "pending", "result": None},
        )

        solicitud = self.despachador.tomar(controlador_ocupado=False)
        self.assertEqual(solicitud.request_id, self.request_id)
        self.assertEqual(solicitud.usuario_id, 7)

    def test_reintento_devuelve_409_y_no_encola_otra_operacion(self):
        primera = self.enviar()
        self.assertEqual(primera.status_code, 202)

        self.presencia.return_value = False
        repetida = self.enviar()

        self.assertEqual(repetida.status_code, 409)
        self.assertEqual(repetida.json(), primera.json())

        solicitud = self.despachador.tomar(controlador_ocupado=False)
        self.assertEqual(solicitud.request_id, self.request_id)
        self.despachador.completar(self.request_id, "autorizado")
        self.assertIsNone(self.despachador.tomar(controlador_ocupado=False))

    def test_otra_sesion_recibe_403_aunque_sea_del_mismo_usuario(self):
        self.assertEqual(self.enviar().status_code, 202)

        respuesta = self.enviar(token="otro-token")

        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(
            respuesta.json(), {"error": "La solicitud pertenece a otra sesión"}
        )

    def test_solicitud_nueva_requiere_presencia_disponible_y_activa(self):
        for presencia, codigo in ((False, 403), (None, 503)):
            with self.subTest(presencia=presencia):
                self.presencia.return_value = presencia
                self.assertEqual(self.enviar().status_code, codigo)
                self.assertIsNone(
                    self.despachador.tomar(controlador_ocupado=False)
                )

    def consultar(self, token="token-prueba"):
        return self.cliente.get(
            f"/access-requests/{self.request_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    def test_consulta_devuelve_el_resultado_aunque_ya_no_haya_presencia(self):
        self.assertEqual(self.enviar().status_code, 202)

        pendiente = self.consultar()
        self.assertEqual(pendiente.status_code, 200)
        self.assertEqual(pendiente.json()["state"], "pending")

        self.despachador.tomar(controlador_ocupado=False)
        self.despachador.completar(self.request_id, "autorizado")
        self.presencia.return_value = False

        respuesta = self.consultar()
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta.json(),
            {
                "request_id": self.request_id,
                "state": "complete",
                "result": "autorizado",
            },
        )

    def test_consulta_desde_otra_sesion_devuelve_403(self):
        self.assertEqual(self.enviar().status_code, 202)

        respuesta = self.consultar(token="otro-token")

        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(
            respuesta.json(), {"error": "La solicitud pertenece a otra sesión"}
        )

    def test_consulta_de_uuid_desconocido_devuelve_404(self):
        respuesta = self.consultar()

        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(respuesta.json(), {"error": "Solicitud no encontrada"})