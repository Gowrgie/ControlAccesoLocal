# Installation / Migration Procedure

Run the database setup and migrations with a MySQL administrator. SQL files
are in `src/scripts_db/`. The application uses the restricted accounts
described below.

## New database

Apply these files in order to a new database:

1. `db_squema.sql` creates the base tables, roles, seed users and operational
   account. Configure that account's password to match the deployment.
2. `add_biometric_table.sql` adds facial embeddings and the `facial` access method.
3. `grant_delete_embeddings.sql` allows replacement of facial samples.
4. `add_user_active_flag.sql` adds `usuarios.activo` and the active embeddings view.
5. `add_mobile_auth.sql` adds `usuarios.clave_hash` and `sesiones_movil`.
6. `add_mobile_method.sql` adds `app_movil` to the access log.

Install the dependencies from `requirements-mobile-api.txt` in the
application's Python environment. From `src/` with that environment active,
backfill existing passcodes:

```sh
python -m scripts_db.hashear_claves --usuario root
```

Then configure the administrative account below.

## Existing database

Skip `db_squema.sql` on an existing database. Check which migrations have
already been applied and run the missing ones in the order above. If any users
still need a mobile hash, run the backfill after `add_mobile_auth.sql`.

## Administrative account

In an administrative MySQL session, create the dedicated account with a
deployment-specific password. Substitute the example value when provisioning
the account. If it already exists, use its configured password or rotate it
with `ALTER USER`.

```sql
CREATE USER 'control_acceso_admin'@'localhost'
    IDENTIFIED BY '<deployment password>';
```

Apply `grant_admin_permissions.sql`. Set `CONTROL_ACCESO_ADMIN_DB_PASSWORD`
in the environment of the process that launches the GUI. For a manual launch
from Bash, enter it without echo and then start the GUI from the same shell:

```bash
read -r -s -p 'Admin database password: ' CONTROL_ACCESO_ADMIN_DB_PASSWORD
printf '\n'
export CONTROL_ACCESO_ADMIN_DB_PASSWORD
```

On an existing deployment, create a test user through the updated GUI and verify
mobile sign-in before removing any legacy grant. Inspect both accounts:

```sql
SHOW GRANTS FOR 'control_acceso_admin'@'localhost';
SHOW GRANTS FOR 'control_acceso'@'localhost';
```

If the operational account has the legacy table-level `INSERT` grant on
`control_acceso.usuarios`, remove it and inspect the grants again. Skip this
step on a fresh database, where the base script grants only `SELECT` on that
table.

```sql
REVOKE INSERT ON control_acceso.usuarios FROM 'control_acceso'@'localhost';
SHOW GRANTS FOR 'control_acceso'@'localhost';
```

| Account | Used by | Privileges |
|---|---|---|
| `control_acceso` | Login, access logging, mobile sessions and facial data | `SELECT` on users and roles, plus operational grants from the migrations. |
| `control_acceso_admin` | Creating users from the GUI | `SELECT` on roles and `SELECT`, `INSERT` on users. |

## Rollback

`rollback_add_mobile_method.sql` removes the mobile mechanism from the enum
only if it has never been used in the access log.
