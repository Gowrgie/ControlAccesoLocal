-- add_mobile_auth.sql
-- LAC-83: Argon2id hash of the passcode and short-lived sessions for the mobile app.
-- Run with an admin account, after add_user_active_flag.sql.
-- Afterwards run hashear_claves.py to fill usuarios.clave_hash for the existing users.

USE control_acceso;

-- 1. usuarios.clave_hash: Argon2id hash of the passcode (NULL until hashear_claves.py fills it).
--    MySQL has no ADD COLUMN IF NOT EXISTS, so the check is done by hand.
SET @columna_existe = (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'control_acceso' AND TABLE_NAME = 'usuarios' AND COLUMN_NAME = 'clave_hash'
);
SET @instruccion = IF(@columna_existe = 0,
    'ALTER TABLE usuarios ADD COLUMN clave_hash VARCHAR(255) NULL',
    'SELECT ''usuarios.clave_hash already exists'' AS info');
PREPARE paso FROM @instruccion;
EXECUTE paso;
DEALLOCATE PREPARE paso;

-- 2. Mobile sessions. Only the SHA-256 of the token is stored, never the token itself.
CREATE TABLE IF NOT EXISTS sesiones_movil (
    id_sesion INT AUTO_INCREMENT PRIMARY KEY,
    token_hash CHAR(64) NOT NULL UNIQUE,
    id_usuario INT NOT NULL,
    creada DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expira DATETIME NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);

-- 3. The restricted user creates, validates and closes sessions.
--    It still cannot UPDATE usuarios: the hashes are written by an administrator.
GRANT SELECT, INSERT, DELETE ON control_acceso.sesiones_movil TO 'control_acceso'@'localhost';
FLUSH PRIVILEGES;