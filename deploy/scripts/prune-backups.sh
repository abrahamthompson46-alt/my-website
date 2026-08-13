#!/usr/bin/env bash
# Apply retention policy to backup directories under $BACKUP_ROOT.
# Usage: sudo bash deploy/scripts/prune-backups.sh
#
# Defaults (override via environment):
#   RETENTION_DAILY=7
#   RETENTION_WEEKLY=4
#   RETENTION_MONTHLY=3
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/backup-common.sh
. "$SCRIPT_DIR/lib/backup-common.sh"

RETENTION_DAILY="${RETENTION_DAILY:-7}"
RETENTION_WEEKLY="${RETENTION_WEEKLY:-4}"
RETENTION_MONTHLY="${RETENTION_MONTHLY:-3}"

prune_category() {
    local category="$1"
    local dir="$BACKUP_ROOT/$category"
    [[ -d "$dir" ]] || return 0

    mapfile -t entries < <(ls -1dt "$dir"/*/ 2>/dev/null || true)
    local total="${#entries[@]}"
    local keep="$RETENTION_DAILY"

    if (( total <= keep )); then
        log_backup_event INFO "Retention: $category has $total backups (keep $keep) — nothing pruned"
        return 0
    fi

    local idx
    for (( idx=keep; idx<total; idx++ )); do
        local target="${entries[$idx]}"
        log_backup_event INFO "Retention: removing old $category backup ${target%/}"
        rm -rf "$target"
    done
}

ensure_backup_layout
prune_category database
prune_category media

# Disk pressure warning (do not auto-delete production data outside BACKUP_ROOT)
USED_PCT="$(df -P "$BACKUP_ROOT" | awk 'NR==2 {gsub(/%/,"",$5); print $5}')"
if [[ -n "$USED_PCT" && "$USED_PCT" -ge 90 ]]; then
    log_backup_event ERROR "Backup volume >= 90% full ($USED_PCT%) — investigate immediately"
    exit 2
fi

log_backup_event INFO "Retention prune complete (daily keep=$RETENTION_DAILY)"
