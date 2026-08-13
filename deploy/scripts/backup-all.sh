#!/usr/bin/env bash
# Run database + media backups, verify artifacts, apply retention pruning.
# Usage: sudo bash deploy/scripts/backup-all.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/backup-common.sh
. "$SCRIPT_DIR/lib/backup-common.sh"

STATUS=0
ensure_backup_layout

run_step() {
    local label="$1"
    shift
    log_backup_event INFO "==> $label"
    if "$@"; then
        log_backup_event INFO "==> $label OK"
    else
        log_backup_event ERROR "==> $label FAILED"
        STATUS=1
    fi
}

run_step "Database backup" bash "$SCRIPT_DIR/backup-database.sh"
run_step "Media backup" bash "$SCRIPT_DIR/backup-media.sh"

if [[ "$STATUS" -eq 0 ]]; then
    LATEST_DB_DIR="$(ls -1dt "$BACKUP_ROOT/database/"* 2>/dev/null | head -n 1 || true)"
    LATEST_MEDIA_DIR="$(ls -1dt "$BACKUP_ROOT/media/"* 2>/dev/null | head -n 1 || true)"
    if [[ -n "$LATEST_DB_DIR" ]]; then
        run_step "Verify latest database backup" bash "$SCRIPT_DIR/verify-backup.sh" "$LATEST_DB_DIR"
    fi
    if [[ -n "$LATEST_MEDIA_DIR" ]]; then
        run_step "Verify latest media backup" bash "$SCRIPT_DIR/verify-backup.sh" "$LATEST_MEDIA_DIR"
    fi
fi

run_step "Retention prune" bash "$SCRIPT_DIR/prune-backups.sh" || true

if [[ "$STATUS" -ne 0 ]]; then
    log_backup_event ERROR "backup-all finished with errors"
    exit "$STATUS"
fi

log_backup_event INFO "backup-all finished successfully"
touch "$BACKUP_ROOT/.last-success"
