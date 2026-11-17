# Installation / Migration Procedure

Reproducible order to set up the `control_acceso` database from scratch, or
to bring an existing one up to date. Run the SQL scripts in this order with
an administrative MySQL account (root or equivalent) — never with
`control_acceso` or `control_acceso_admin` themselves.

1. `db_squema.sql` — creates the database, base tables, roles, seed users,
   and the **operational** account `control_acceso` (least privilege:
   `SELECT` on `usuarios`/`roles`, `INSERT` on `intentos_acceso`).
2. `add_biometric_table.sql` — adds `embeddings_faciales` and the `facial`
   access method.
3. `grant_delete_embeddings.sql` — lets `control_acceso` delete face
   samples (re-enrollment).
4. `add_user_active_flag.sql` — adds `usuarios.activo` and the
   `embeddings_faciales_activos` view.
5. `add_mobile_auth.sql` — adds `usuarios.clave_hash` and `sesiones_movil`
   for the mobile app.
6. `add_mobile_method.sql` — adds `app_movil` to the access log's
   `mecanismo` enum.
7. `create_admin_account.sql` — creates the **administrative** account
   `control_acceso_admin` (least privilege: `SELECT` on `roles`,
   `SELECT`+`INSERT` on `usuarios` — exactly what creating a user needs,
   nothing else).
8. `hashear_claves.py` (Python, run once) — fills `usuarios.clave_hash` for
   existing users with an Argon2id hash.

## Accounts

| Account | Used by | Privileges |
|---|---|---|
| `control_acceso` | Day-to-day operation: login validation, access logging, mobile sessions/requests, facial data | Minimal — only what each operational feature reads/writes, built up incrementally across the migrations above. No write access to `usuarios`. |
| `control_acceso_admin` | Administrative path: creating users from the GUI's admin menu (`db_conexion_admin.py`) | `SELECT` on `roles`; `SELECT`+`INSERT` on `usuarios`. No access to `intentos_acceso`, `sesiones_movil`, or `embeddings_faciales` — the admin path has no business there. |

Before production use, change both accounts' default passwords
(`cambia_esta_password` / `cambia_esta_password_admin`) and update
`db_conexion.py`/`db_conexion_admin.py` accordingly.

## Rollback

Only `add_mobile_method.sql` has a scripted rollback
(`rollback_add_mobile_method.sql`), and it refuses to run once the mobile
method has real usage logged, by design — access history is never deleted
or altered.