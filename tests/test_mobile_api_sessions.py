import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.app import crear_api


class PruebaApiSesiones(unittest.TestCase):
    def setUp(self):
        self.cliente = TestClient(crear_api())
        self.addCleanup(self.cliente.close)
        self.credenciales = {
            "identificador": "usuario-prueba",
            "clave": "clave-prueba",
        }

    def test_login_devuelve_token_y_expiracion(self):
        expira = datetime(2030, 1, 1, 12, 10, tzinfo=timezone.utc)
        sesion = {"token": "token-prueba", "expira": expira}

        with patch(
            "api.app.autenticacion.iniciar_sesion", return_value=sesion
        ) as iniciar_sesion:
            respuesta = self.cliente.post("/sessions", json=self.credenciales)

        iniciar_sesion.assert_called_once_with("usuario-prueba", "clave-prueba")
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertEqual(set(datos), {"token", "expira"})
        self.assertEqual(datos["token"], "token-prueba")
        fecha = datetime.fromisoformat(datos["expira"].replace("Z", "+00:00"))
        self.assertEqual(fecha, expira)

    def test_login_invalido_devuelve_401_con_error(self):
        with patch("api.app.autenticacion.iniciar_sesion", return_value=None):
            respuesta = self.cliente.post("/sessions", json=self.credenciales)

        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.json(), {"error": "Credenciales inválidas"})

    def test_logout_devuelve_204_aunque_el_token_ya_este_revocado(self):
        encabezados = {"Authorization": "Bearer token-prueba"}

        with patch(
            "api.app.autenticacion.cerrar_sesion", side_effect=[1, 0]
        ) as cerrar_sesion:
            for _ in range(2):
                respuesta = self.cliente.delete("/sessions", headers=encabezados)
                self.assertEqual(respuesta.status_code, 204)
                self.assertEqual(respuesta.content, b"")

        self.assertEqual(cerrar_sesion.call_count, 2)
        cerrar_sesion.assert_called_with("token-prueba")

    def test_logout_sin_token_devuelve_401(self):
        with patch("api.app.autenticacion.cerrar_sesion") as cerrar_sesion:
            respuesta = self.cliente.delete("/sessions")

        self.assertEqual(respuesta.status_code, 401)
        cerrar_sesion.assert_not_called()

    def test_login_incompleto_devuelve_422_sin_exponer_la_clave(self):
        with patch("api.app.autenticacion.iniciar_sesion") as autenticar:
            respuesta = self.cliente.post(
                "/sessions", json={"clave": "secreto-de-prueba"}
            )

        self.assertEqual(respuesta.status_code, 422)
        self.assertEqual(respuesta.json(), {"error": "Datos de solicitud inválidos"})
        autenticar.assert_not_called()