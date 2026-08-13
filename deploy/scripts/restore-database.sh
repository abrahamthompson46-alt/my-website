#!/usr/bin/env bash
# Restore a pg_dump custom-format backup into a target PostgreSQL database.
#
# Authentication split:
#   - Admin DDL (terminate/drop/create DB): local postgres OS user + peer auth
#     via pg_admin_* helpers in lib/backup-common.sh (no postgres role password).
#   - pg_restore + validation: application DB_USER over TCP using DB_PASSWORD.
#
# Usage (disposable/test database):
#   RESTORE_TARGET_DB=zreta_restore_test \
#   bash deploy/scripts/restore-database.sh /var/backups/zreta/database/YYYYMMDD-HHMMSS
#
# SAFETY: Requires RESTORE_TARGET_DB. Refuses to restore into production DB_NAME
# unless RESTORE_ALLOW_PRODUCTION=1 is explicitly set.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/backup-common.sh
. "$SCRIPT_DIR/lib/backup-common.sh"

BACKUP_DIR="${1:-}"
RESTORE_TARGET_DB="${RESTORE_TARGET_DB:-}"

if [[ -z "$BACKUP_DIR" || ! -d "$BACKUP_DIR" ]]; then
    echo "Usage: RESTORE_TARGET_DB=<name> restore-database.sh <backup-directory>" >&2
    exit 1
fi

if [[ -z "$RESTORE_TARGET_DB" ]]; then
    echo "RESTORE_TARGET_DB is required (use a disposable database name)." >&2
    exit 1
fi

if ! validate_pg_identifier "$RESTORE_TARGET_DB"; then
    exit 1
fi
RESTORE_TARGET_DB="$(normalize_pg_identifier "$RESTORE_TARGET_DB")"

require_command pg_restore
require_command psql
require_command createdb

load_database_env

if is_production_db_name "$RESTORE_TARGET_DB" "$DB_NAME" && [[ "${RESTORE_ALLOW_PRODUCTION:-0}" != "1" ]]; then
    echo "Refusing to restore into production database '$DB_NAME'." >&2
    echo "Set RESTORE_ALLOW_PRODUCTION=1 only during a controlled disaster recovery." >&2
    exit 1
fi

MANIFEST="$BACKUP_DIR/manifest.json"
bash "$SCRIPT_DIR/verify-backup.sh" "$BACKUP_DIR"

ARTIFACT_NAME="$(python3 - <<'PY' "$MANIFEST"
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["artifact"])
PY
)"
if ! is_safe_manifest_artifact "$ARTIFACT_NAME"; then
    echo "Unsafe artifact path in manifest: $ARTIFACT_NAME" >&2
    exit 1
fi
DUMP_FILE="$BACKUP_DIR/$ARTIFACT_NAME"

log_backup_event INFO "Restoring $DUMP_FILE -> database $RESTORE_TARGET_DB"

# Admin DDL: local postgres OS user + peer auth (see backup-common.sh).
pg_admin_terminate_connections "$RESTORE_TARGET_DB"
pg_admin_drop_database "$RESTORE_TARGET_DB"
pg_admin_create_database "$RESTORE_TARGET_DB" "$DB_USER"

# Restore + smoke query: application role over TCP (DB_PASSWORD from .env).
pg_restore \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$RESTORE_TARGET_DB" \
    --no-owner \
    --no-acl \
    --exit-on-error \
    "$DUMP_FILE"

psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$RESTORE_TARGET_DB" -v ON_ERROR_STOP=1 \
    -c "SELECT current_database() AS restored_db, COUNT(*) AS auth_user_rows FROM auth_user;" >/dev/null

log_backup_event INFO "Restore complete into $RESTORE_TARGET_DB"
unset PGPASSWORD
