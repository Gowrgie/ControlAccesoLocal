-- grant_delete_embeddings.sql
-- LAC-71: lets the restricted application user delete face samples
-- (re-enrollment, removal of a user's biometric data).
-- The privilege is limited to embeddings_faciales. Run with an admin account,
-- after add_biometric_table.sql.

USE control_acceso;

GRANT DELETE ON control_acceso.embeddings_faciales TO 'control_acceso'@'localhost';
FLUSH PRIVILEGES;