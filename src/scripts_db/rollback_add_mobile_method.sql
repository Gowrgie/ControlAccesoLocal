-- rollback_add_mobile_method.sql
-- LAC-100: undoes add_mobile_method.sql (the access log stops accepting "app_movil").
-- Non-destructive: audit records are never deleted or changed. If any attempt already
-- uses app_movil, the rollback is REFUSED with an error and nothing is altered.
-- Run with an admin account. Once the mobile app has logged attempts, this rollback
-- is no longer possible by design.
--
-- To see how many attempts would block it:
--   SELECT COUNT(*) FROM intentos_acceso WHERE mecanismo = 'app_movil';

USE control_acceso;

-- Strict mode for this session: a value in use can never be silently blanked.
SET SESSION sql_mode = CONCAT_WS(',', @@SESSION.sql_mode, 'STRICT_TRANS_TABLES');

SET @tipo = (
    SELECT COLUMN_TYPE FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'control_acceso' AND TABLE_NAME = 'intentos_acceso' AND COLUMN_NAME = 'mecanismo'
);
SET @en_uso = (SELECT COUNT(*) FROM intentos_acceso WHERE mecanismo = 'app_movil');

-- When attempts use app_movil the statement below fails on purpose: the missing
-- table name in the error message is the reason for the refusal.
SET @instruccion = IF(@tipo IS NULL OR @tipo NOT LIKE '%''app_movil''%',
    'SELECT ''nothing to roll back: app_movil is not in intentos_acceso.mecanismo'' AS info',
    IF(@en_uso > 0,
        'SELECT * FROM rollback_refused_attempts_already_use_app_movil',
        CONCAT('ALTER TABLE intentos_acceso MODIFY mecanismo ',
               REPLACE(@tipo, ',''app_movil''', ''), ' NOT NULL')));

PREPARE paso FROM @instruccion;
EXECUTE paso;
DEALLOCATE PREPARE paso;