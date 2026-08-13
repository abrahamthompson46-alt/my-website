"""PostgreSQL restore authentication policy for deploy/scripts DR tooling."""

from __future__ import annotations

from pathlib import Path

# Cluster-admin DDL: postgres OS user, Unix socket peer auth (sudo -u postgres).
PG_ADMIN_AUTH_MODE = "local_peer"

# pg_restore and post-restore validation: application DB_USER + DB_PASSWORD over TCP.
PG_APP_AUTH_MODE = "password_tcp"

FORBIDDEN_ADMIN_PATTERNS = (
    "PSQL_ADMIN_USER",
    '-U "$PSQL_ADMIN_USER"',
)

REQUIRED_ADMIN_HELPER_DEFINITIONS = (
    "pg_run_local_admin",
    "pg_admin_terminate_connections",
    "pg_admin_drop_database",
    "pg_admin_create_database",
)

REQUIRED_ADMIN_HELPER_CALLS = (
    "pg_admin_terminate_connections",
    "pg_admin_drop_database",
    "pg_admin_create_database",
)

REQUIRED_APP_RESTORE_FLAGS = (
    '--username="$DB_USER"',
    "--no-owner",
    "--no-acl",
    "--exit-on-error",
)

# Django AUTH_USER_MODEL=accounts.User → table public.accounts_user (not auth_user).
CUSTOM_USER_TABLE = "public.accounts_user"
FORBIDDEN_USER_TABLE_REFERENCES = (
    "FROM auth_user",
    "from auth_user",
)


def read_repo_file(relative_path: str) -> str:
    return Path(relative_path).read_text(encoding="utf-8")


def restore_script_uses_local_peer_admin(script_text: str) -> bool:
    """Admin DDL must not password-authenticate the postgres role over TCP."""
    if any(pattern in script_text for pattern in FORBIDDEN_ADMIN_PATTERNS):
        return False
    return all(helper in script_text for helper in REQUIRED_ADMIN_HELPER_CALLS)


def restore_script_uses_app_user_for_pg_restore(script_text: str) -> bool:
    return all(flag in script_text for flag in REQUIRED_APP_RESTORE_FLAGS)


def backup_common_defines_local_admin_helpers(script_text: str) -> bool:
    if "sudo -u" not in script_text or "PG_LOCAL_ADMIN_OS_USER" not in script_text:
        return False
    return all(helper in script_text for helper in REQUIRED_ADMIN_HELPER_DEFINITIONS)


def drill_script_uses_local_admin_for_cleanup(script_text: str) -> bool:
    if "PSQL_ADMIN_USER" in script_text:
        return False
    return "pg_admin_drop_database" in script_text


def restore_scripts_validate_custom_user_table(*script_texts: str) -> bool:
    """Post-restore smoke queries must count rows from public.accounts_user."""
    combined = "\n".join(script_texts)
    if any(ref in combined for ref in FORBIDDEN_USER_TABLE_REFERENCES):
        return False
    return CUSTOM_USER_TABLE in combined
