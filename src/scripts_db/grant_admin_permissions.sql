-- LAC-101: grant the privileges used by the GUI's user creation flow.
-- Run as a MySQL administrator after provisioning control_acceso_admin.
-- See documentacion/installation.md for account setup and upgrade ordering.

GRANT SELECT ON control_acceso.roles TO 'control_acceso_admin'@'localhost';
GRANT SELECT, INSERT ON control_acceso.usuarios TO 'control_acceso_admin'@'localhost';
