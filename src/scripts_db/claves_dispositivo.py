"""Public-key validation for Android device credentials."""

from base64 import b64decode

from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    load_der_public_key,
)


def _leer_clave(der):
    try:
        clave = load_der_public_key(der)
    except UnsupportedAlgorithm as error:
        raise ValueError("Algoritmo de clave no admitido") from error
    if not isinstance(clave, ec.EllipticCurvePublicKey) or not isinstance(clave.curve, ec.SECP256R1):
        raise ValueError("Se requiere una clave pública P-256")
    return clave


def decodificar_clave_publica(valor):
    der = b64decode(valor, validate=True)
    if len(der) > 120:
        raise ValueError("Clave pública demasiado larga")
    return _leer_clave(der).public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)


def verificar_firma(der, mensaje, firma):
    try:
        _leer_clave(der).verify(firma, mensaje, ec.ECDSA(hashes.SHA256()))
    except (InvalidSignature, ValueError):
        return False
    return True
