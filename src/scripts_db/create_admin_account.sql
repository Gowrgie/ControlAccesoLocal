-- create_admin_account.sql
-- LAC-101: dedicated least-privilege account for the administrative path
-- (creating users from the admin menu), separate from the operational
-- account (control_acceso) used for everyday login and attempt logging.
-- Run with an admin/root account, after db_squema.sql.

USE control_acceso;

CREATE USER IF NOT EXISTS 'control_acceso_admin'@'localhost'
    IDENTIFIED BY 'cambia_esta_password_admin';

-- Exactly what crear_usuario() needs: read roles, read+create users.
-- No access to intentos_acceso, sesiones_movil or embeddings_faciales --
-- the administrative path has no business with those tables.
GRANT SELECT ON control_acceso.roles TO 'control_acceso_admin'@'localhost';
GRANT SELECT, INSERT ON control_acceso.usuarios TO 'control_acceso_admin'@'localhost';

FLUSH PRIVILEGES;