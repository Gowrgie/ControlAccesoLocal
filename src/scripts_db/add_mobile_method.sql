-- add_mobile_method.sql
-- LAC-100: the access log accepts the mobile app ("app_movil") as an access method.
-- Non-destructive: app_movil is appended at the END of the ENUM and the existing
-- values are read from the table itself, so no row and no existing value is lost.
-- Safe to run more than once. Run with an admin account, after add_biometric_table.sql.
-- Undo it with rollback_add_mobile_method.sql.

USE control_acceso;

-- Current definition of the column, for example: enum('interfaz_grafica','botones','facial')
SET @tipo = (
    SELECT COLUMN_TYPE FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'control_acceso' AND TABLE_NAME = 'intentos_acceso' AND COLUMN_NAME = 'mecanismo'
);

SET @instruccion = IF(@tipo IS NULL,
    'SELECT ''intentos_acceso.mecanismo not found: apply db_squema.sql first'' AS info',
    IF(@tipo LIKE '%''app_movil''%',
        'SELECT ''intentos_acceso.mecanismo already accepts app_movil'' AS info',
        CONCAT('ALTER TABLE intentos_acceso MODIFY mecanismo ',
               LEFT(@tipo, LENGTH(@tipo) - 1), ',''app_movil'') NOT NULL')));

PREPARE paso FROM @instruccion;
EXECUTE paso;
DEALLOCATE PREPARE paso;