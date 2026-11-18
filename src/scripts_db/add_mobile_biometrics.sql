-- LAC-123: public keys for devices linked through a password sign-in.
USE control_acceso;

CREATE TABLE IF NOT EXISTS credenciales_biometricas_movil (
    id_credencial CHAR(32) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
    id_usuario INT NOT NULL,
    clave_publica VARBINARY(120) NOT NULL,
    creada DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);

GRANT SELECT, INSERT ON control_acceso.credenciales_biometricas_movil
TO 'control_acceso'@'localhost';
