#!/usr/bin/env bash
# Non-production disaster-recovery drill.
#
# Creates a disposable database, restores the latest (or specified) backup into it,
# runs basic PostgreSQL validation, then drops the disposable database.
#
# Usage on VPS/staging (NOT production emergency restore):
#   sudo bash deploy/scripts/test-restore-drill.sh
#   sudo bash deploy/scripts/test-restore-drill.sh /var/backups/zreta/database/YYYYMMDD-HHMMSS
#
# Requires: PostgreSQL client tools, existing backup directory.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/backup-common.sh
. "$SCRIPT_DIR/lib/backup-common.sh"

# Never inherit production-restore opt-in from the operator shell.
unset RESTORE_ALLOW_PRODUCTION

BACKUP_DIR="${1:-}"
if [[ -z "$BACKUP_DIR" ]]; then
    BACKUP_DIR="$(ls -1dt "$BACKUP_ROOT/database/"* 2>/dev/null | head -n 1 || true)"
fi

if [[ -z "$BACKUP_DIR" || ! -d "$BACKUP_DIR" ]]; then
    echo "No database backup directory found under $BACKUP_ROOT/database" >&2
    exit 1
fi

export RESTORE_TARGET_DB="${RESTORE_TARGET_DB:-zreta_restore_drill}"
if ! validate_pg_identifier "$RESTORE_TARGET_DB"; then
    exit 1
fi
RESTORE_TARGET_DB="$(normalize_pg_identifier "$RESTORE_TARGET_DB")"
export RESTORE_TARGET_DB

load_database_env

if is_production_db_name "$RESTORE_TARGET_DB" "$DB_NAME"; then
    echo "DR drill refuses production database target '$RESTORE_TARGET_DB'." >&2
    exit 1
fi

DRILL_DB="$RESTORE_TARGET_DB"
PSQL_ADMIN_USER="${PSQL_ADMIN_USER:-postgres}"

cleanup_drill_db() {
    if [[ "${RESTORE_DRILL_KEEP_DB:-0}" == "1" || -z "${DRILL_DB:-}" ]]; then
        return 0
    fi
    load_database_env
    dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$PSQL_ADMIN_USER" "$DRILL_DB" >/dev/null 2>&1 || true
    log_backup_event INFO "DR drill dropped disposable database $DRILL_DB"
    unset PGPASSWORD
}

trap cleanup_drill_db EXIT

log_backup_event INFO "DR drill: backup=$BACKUP_DIR target=$DRILL_DB"

bash "$SCRIPT_DIR/restore-database.sh" "$BACKUP_DIR"

psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DRILL_DB" -v ON_ERROR_STOP=1 <<'SQL'
SELECT current_database() AS db;
SELECT COUNT(*) AS django_migrations FROM django_migrations;
SELECT COUNT(*) AS users FROM auth_user;
SQL

log_backup_event INFO "DR drill validation queries OK"

log_backup_event INFO "DR drill PASSED"
