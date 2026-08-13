#!/usr/bin/env bash
# Shared helpers for Zreta backup/restore scripts.
# Source from other scripts: . "$(dirname "$0")/lib/backup-common.sh"
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/marketing-site}"
ENV_FILE="${ENV_FILE:-$APP_DIR/.env}"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/zreta}"
BACKUP_LOG_DIR="${BACKUP_LOG_DIR:-/var/log/zreta-backup}"

timestamp_utc() {
    date -u +"%Y%m%d-%H%M%S"
}

require_command() {
    local cmd="$1"
    command -v "$cmd" >/dev/null 2>&1 || {
        echo "Required command not found: $cmd" >&2
        exit 1
    }
}

# PostgreSQL folds unquoted identifiers to lowercase.
normalize_pg_identifier() {
    printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

validate_pg_identifier() {
    local name="$1"
    if [[ ! "$name" =~ ^[a-zA-Z_][a-zA-Z0-9_]{0,62}$ ]]; then
        echo "Invalid PostgreSQL database name: '$name' (letters, digits, underscore; max 63 chars)." >&2
        return 1
    fi
}

is_production_db_name() {
    local target="$1"
    local production="$2"
    [[ "$(normalize_pg_identifier "$target")" == "$(normalize_pg_identifier "$production")" ]]
}

is_safe_manifest_artifact() {
    local name="$1"
    [[ -n "$name" && "$name" == "$(basename "$name")" && "$name" != *"/"* && "$name" != *".."* ]]
}

# Load selected keys from Django .env without eval/sourcing the full file.
load_env_var() {
    local key="$1"
    local file="${2:-$ENV_FILE}"
    if [[ ! -f "$file" ]]; then
        return 1
    fi
    local line
    line="$(grep -E "^${key}=" "$file" | tail -n 1 || true)"
    if [[ -z "$line" ]]; then
        return 1
    fi
    printf '%s' "${line#${key}=}" | sed -e 's/^["'\'' ]*//' -e 's/["'\'' ]*$//'
}

load_database_env() {
    DB_ENGINE="$(load_env_var DB_ENGINE || echo django.db.backends.postgresql)"
    DB_NAME="$(load_env_var DB_NAME || echo marketing)"
    DB_USER="$(load_env_var DB_USER || echo marketing)"
    DB_PASSWORD="$(load_env_var DB_PASSWORD || true)"
    DB_HOST="$(load_env_var DB_HOST || echo 127.0.0.1)"
    DB_PORT="$(load_env_var DB_PORT || echo 5432)"

    if [[ -z "${DB_PASSWORD:-}" ]]; then
        echo "DB_PASSWORD is not set in $ENV_FILE" >&2
        exit 1
    fi
    if [[ "$DB_ENGINE" != *postgresql* ]]; then
        echo "Backup scripts require PostgreSQL (DB_ENGINE=$DB_ENGINE)" >&2
        exit 1
    fi
    export PGPASSWORD="$DB_PASSWORD"
}

ensure_backup_layout() {
    mkdir -p "$BACKUP_ROOT"/{database,media,manifests}
    mkdir -p "$BACKUP_LOG_DIR"
    chmod 700 "$BACKUP_ROOT" 2>/dev/null || true
    chmod 750 "$BACKUP_LOG_DIR" 2>/dev/null || true
}

write_manifest_json() {
    local manifest_path="$1"
    local backup_type="$2"
    local artifact_path="$3"
    local db_name="${4:-}"
    local size_bytes
    size_bytes="$(wc -c <"$artifact_path" | tr -d ' ')"
    local sha256
    sha256="$(sha256sum "$artifact_path" | awk '{print $1}')"
    cat >"$manifest_path" <<EOF
{
  "schema_version": 1,
  "backup_type": "$backup_type",
  "created_at_utc": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "hostname": "$(hostname -f 2>/dev/null || hostname)",
  "app_dir": "$APP_DIR",
  "database_name": "$db_name",
  "artifact": "$(basename "$artifact_path")",
  "size_bytes": $size_bytes,
  "sha256": "$sha256"
}
EOF
}

log_backup_event() {
    local level="$1"
    shift
    local msg="$*"
    local log_file="$BACKUP_LOG_DIR/backup.log"
    printf '%s [%s] %s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$level" "$msg" | tee -a "$log_file"
    chmod 640 "$log_file" 2>/dev/null || true
}

# --- PostgreSQL restore: authentication split ---
#
# Admin DDL (terminate backends, drop/create database) runs as the local cluster
# OS user (postgres) via Unix-domain peer authentication:
#   sudo -u postgres psql|dropdb|createdb   (no -h, no -U, no PGPASSWORD)
#
# Restore and validation run as the application role (DB_USER) over TCP using
# credentials from .env (PGPASSWORD / DB_PASSWORD). The marketing user must not
# receive cluster-admin privileges.
PG_LOCAL_ADMIN_OS_USER="${PG_LOCAL_ADMIN_OS_USER:-postgres}"

pg_run_local_admin() {
    # Prevent client tools from using the application password against the postgres role.
    local saved_pgpassword="${PGPASSWORD:-}"
    unset PGPASSWORD

    local rc=0
    if [[ "$(id -un)" == "$PG_LOCAL_ADMIN_OS_USER" ]]; then
        "$@" || rc=$?
    elif [[ "$(id -u)" -eq 0 ]] || command -v sudo >/dev/null 2>&1; then
        require_command sudo
        sudo -u "$PG_LOCAL_ADMIN_OS_USER" -- "$@" || rc=$?
    else
        echo "PostgreSQL admin operation requires root or the $PG_LOCAL_ADMIN_OS_USER OS user (peer auth)." >&2
        echo "Run via: sudo bash deploy/scripts/test-restore-drill.sh" >&2
        rc=1
    fi

    if [[ -n "$saved_pgpassword" ]]; then
        export PGPASSWORD="$saved_pgpassword"
    fi
    return "$rc"
}

pg_admin_terminate_connections() {
    local db_name="$1"
    pg_run_local_admin psql -d postgres -v ON_ERROR_STOP=1 \
        -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${db_name}' AND pid <> pg_backend_pid();" \
        >/dev/null 2>&1 || true
}

pg_admin_drop_database() {
    local db_name="$1"
    pg_run_local_admin dropdb --if-exists "$db_name" >/dev/null 2>&1 || true
}

pg_admin_create_database() {
    local db_name="$1"
    local owner_user="$2"
    pg_run_local_admin createdb -O "$owner_user" "$db_name"
}
