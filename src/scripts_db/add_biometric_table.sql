-- add_biometric_table.sql
-- Migration for an existing control_acceso database.
-- Adds facial embeddings storage and the facial authentication method.
-- Run it with an admin account (not control_acceso).

USE control_acceso;

-- 1. New table: facial embeddings linked to users (one user, several samples)
CREATE TABLE IF NOT EXISTS embeddings_faciales (
    id_embedding INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    embedding BLOB NOT NULL,
    modelo VARCHAR(50) NOT NULL,
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);

-- 2. Existing table change: access log accepts the facial method
ALTER TABLE intentos_acceso
    MODIFY mecanismo ENUM('interfaz_grafica', 'botones', 'facial') NOT NULL;

-- 3. Permissions: restricted user can read and insert, nothing else
GRANT SELECT, INSERT ON control_acceso.embeddings_faciales TO 'control_acceso'@'localhost';
FLUSH PRIVILEGES;