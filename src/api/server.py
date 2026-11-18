import ssl
from threading import Thread

import uvicorn

from api.app import crear_api


class ServidorApiMovil:
    def __init__(self, control, *, host, puerto=8000, certificado, clave_privada):
        if not certificado or not clave_privada:
            raise ValueError("HTTPS requiere un certificado y una clave privada")

        api = crear_api(
            obtener_presencia=control.consultar_presencia_movil,
            despachador=control.despachador,
        )

        config = uvicorn.Config(
            api,
            host=host,
            port=puerto,
            loop="asyncio",
            workers=1,
            proxy_headers=False,
            access_log=False,
            ssl_certfile=certificado,
            ssl_keyfile=clave_privada,
            ssl_version=ssl.PROTOCOL_TLS_SERVER,
            timeout_graceful_shutdown=5,
        )
        config.load()
        config.ssl.minimum_version = ssl.TLSVersion.TLSv1_2

        self._servidor = uvicorn.Server(config)
        self._hilo = Thread(
            target=self._servidor.run,
            name="api-movil",
            daemon=True,
        )

    def iniciar(self):
        self._hilo.start()

    def cerrar(self):
        self._servidor.should_exit = True
        if self._hilo.ident is not None:
            self._hilo.join(timeout=6)