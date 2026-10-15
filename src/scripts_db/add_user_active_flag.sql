USE control_acceso;

-- 1. New column usuarios.activo (existing users stay active).
--    MySQL has no ADD COLUMN IF NOT EXISTS, so the check is done by hand.
SET @columna_existe = (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'control_acceso' AND TABLE_NAME = 'usuarios' AND COLUMN_NAME = 'activo'
);
SET @instruccion = IF(@columna_existe = 0,
    'ALTER TABLE usuarios ADD COLUMN activo BOOLEAN NOT NULL DEFAULT TRUE',
    'SELECT ''usuarios.activo already exists'' AS info');
PREPARE paso FROM @instruccion;
EXECUTE paso;
DEALLOCATE PREPARE paso;

-- 2. View with the embeddings of active users only.
CREATE OR REPLACE VIEW embeddings_faciales_activos AS
    SELECT e.id_embedding, e.id_usuario, e.embedding, e.modelo, e.fecha_registro
    FROM embeddings_faciales e
    JOIN usuarios u ON u.id_usuario = e.id_usuario
    WHERE u.activo = TRUE;

-- 3. The restricted user reads face data through the view.
GRANT SELECT ON control_acceso.embeddings_faciales_activos TO 'control_acceso'@'localhost';
FLUSH PRIVILEGES;