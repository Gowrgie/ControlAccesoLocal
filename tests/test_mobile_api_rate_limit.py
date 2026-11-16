import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from uuid import uuid4

from access_dispatcher import DespachadorAcceso

from fastapi.testclient import TestClient

from api.app import crear_api


class PruebaLimitesLogin(unittest.TestCase):
    def setUp(self):
        self.ahora = 0

    def crear_cliente(self, *, limite_ip, limite_identificador):
        cliente = TestClient(
            crear_api(
                reloj=lambda: self.ahora,
                limite_login_ip=limite_ip,
                limite_login_identificador=limite_identificador,
            )
        )
        self.addCleanup(cliente.close)
        return cliente

    def iniciar_sesion(self, cliente, identificador="usuario-prueba"):
        return cliente.post(
            "/sessions",
            json={"identificador": identificador, "clave": "clave-prueba"},
        )

    def test_limite_por_identificador_y_reapertura_de_la_ventana(self):
        cliente = self.crear_cliente(limite_ip=10, limite_identificador=2)

        with patch(
            "api.app.autenticacion.iniciar_sesion", return_value=None
        ) as autenticar:
            self.assertEqual(self.iniciar_sesion(cliente).status_code, 401)
            self.assertEqual(self.iniciar_sesion(cliente).status_code, 401)

            bloqueada = self.iniciar_sesion(cliente)
            self.assertEqual(bloqueada.status_code, 429)
            self.assertEqual(bloqueada.headers["Retry-After"], "60")

            self.ahora = 59
            bloqueada = self.iniciar_sesion(cliente)
            self.assertEqual(bloqueada.status_code, 429)
            self.assertEqual(bloqueada.headers["Retry-After"], "1")
            self.assertEqual(autenticar.call_count, 2)

            self.ahora = 60
            self.assertEqual(self.iniciar_sesion(cliente).status_code, 401)
            self.assertEqual(autenticar.call_count, 3)

    def test_limite_por_ip_aplica_a_distintos_identificadores(self):
        cliente = self.crear_cliente(limite_ip=2, limite_identificador=5)

        with patch(
            "api.app.autenticacion.iniciar_sesion", return_value=None
        ) as autenticar:
            self.assertEqual(self.iniciar_sesion(cliente, "usuario-a").status_code, 401)
            self.assertEqual(self.iniciar_sesion(cliente, "usuario-b").status_code, 401)

            bloqueada = self.iniciar_sesion(cliente, "usuario-c")
            self.assertEqual(bloqueada.status_code, 429)
            self.assertEqual(bloqueada.headers["Retry-After"], "60")
            self.assertEqual(autenticar.call_count, 2)

    def test_login_exitoso_libera_la_reserva_del_identificador(self):
        cliente = self.crear_cliente(limite_ip=10, limite_identificador=1)
        sesion = {
            "token": "token-prueba",
            "expira": datetime(2030, 1, 1, 12, 10, tzinfo=timezone.utc),
        }

        with patch(
            "api.app.autenticacion.iniciar_sesion", return_value=sesion
        ) as autenticar:
            self.assertEqual(self.iniciar_sesion(cliente).status_code, 200)
            self.assertEqual(self.iniciar_sesion(cliente).status_code, 200)
            self.assertEqual(autenticar.call_count, 2)

class PruebaLimitesAcceso(unittest.TestCase):
    def setUp(self):
        cliente = TestClient(
            crear_api(
                obtener_presencia=lambda: True,
                despachador=DespachadorAcceso(),
                reloj=lambda: 0,
                limite_aperturas_usuario=2,
                limite_consultas_sesion=2,
            )
        )
        self.cliente = cliente
        self.addCleanup(cliente.close)

    def encabezados(self, token):
        return {"Authorization": f"Bearer {token}"}

    def enviar(self, request_id, token):
        return self.cliente.post(
            "/access-requests",
            json={"request_id": request_id},
            headers=self.encabezados(token),
        )

    def test_dos_tokens_del_mismo_usuario_comparten_el_limite_de_aperturas(self):
        usuarios = {"token-a": 7, "token-b": 7, "token-c": 8}
        request_id = str(uuid4())

        with patch(
            "api.app.autenticacion.validar_sesion", side_effect=usuarios.get
        ):
            self.assertEqual(self.enviar(request_id, "token-a").status_code, 202)
            self.assertEqual(self.enviar(request_id, "token-a").status_code, 409)

            bloqueada = self.enviar(str(uuid4()), "token-b")
            self.assertEqual(bloqueada.status_code, 429)
            self.assertEqual(bloqueada.headers["Retry-After"], "60")

            self.assertEqual(self.enviar(str(uuid4()), "token-c").status_code, 202)

    def test_presencia_y_estado_comparten_el_limite_por_sesion(self):
        request_id = str(uuid4())
        encabezados = self.encabezados("token-a")

        with patch("api.app.autenticacion.validar_sesion", return_value=7):
            self.assertEqual(self.enviar(request_id, "token-a").status_code, 202)
            self.assertEqual(
                self.cliente.get("/presence", headers=encabezados).status_code,
                200,
            )
            self.assertEqual(
                self.cliente.get(
                    f"/access-requests/{request_id}", headers=encabezados
                ).status_code,
                200,
            )

            bloqueada = self.cliente.get("/presence", headers=encabezados)
            self.assertEqual(bloqueada.status_code, 429)
            self.assertEqual(bloqueada.headers["Retry-After"], "60")

            otra_sesion = self.cliente.get(
                "/presence", headers=self.encabezados("token-b")
            )
            self.assertEqual(otra_sesion.status_code, 200)