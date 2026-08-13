#!/usr/bin/env bash
# PostgreSQL logical backup for Zreta (pg_dump custom format).
# Usage: sudo bash deploy/scripts/backup-database.sh
#
# Reads DB_* credentials from $APP_DIR/.env — passwords are never echoed.
# Does not require Django to be running.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/backup-common.sh
. "$SCRIPT_DIR/lib/backup-common.sh"

require_command pg_dump
require_command sha256sum

ensure_backup_layout
load_database_env

STAMP="$(timestamp_utc)"
DEST_DIR="$BACKUP_ROOT/database/$STAMP"
mkdir -p "$DEST_DIR"
chmod 700 "$DEST_DIR"

DUMP_FILE="$DEST_DIR/${DB_NAME}-${STAMP}.pgdump"
MANIFEST="$DEST_DIR/manifest.json"

log_backup_event INFO "Starting database backup db=$DB_NAME host=$DB_HOST"

pg_dump \
    --format=custom \
    --no-owner \
    --no-acl \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --file="$DUMP_FILE" \
    "$DB_NAME"

if [[ ! -s "$DUMP_FILE" ]]; then
    log_backup_event ERROR "Database backup file is empty: $DUMP_FILE"
    exit 1
fi

write_manifest_json "$MANIFEST" "database" "$DUMP_FILE" "$DB_NAME"
chmod 600 "$DUMP_FILE" "$MANIFEST"

log_backup_event INFO "Database backup complete: $DUMP_FILE ($(wc -c <"$DUMP_FILE" | tr -d ' ') bytes)"

unset PGPASSWORD
