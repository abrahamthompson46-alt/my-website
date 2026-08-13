#!/usr/bin/env bash
# Verify a backup directory (manifest checksum + artifact integrity).
# Usage: bash deploy/scripts/verify-backup.sh /var/backups/zreta/database/YYYYMMDD-HHMMSS
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/backup-common.sh
. "$SCRIPT_DIR/lib/backup-common.sh"

BACKUP_DIR="${1:-}"
if [[ -z "$BACKUP_DIR" || ! -d "$BACKUP_DIR" ]]; then
    echo "Usage: verify-backup.sh <backup-directory>" >&2
    exit 1
fi

MANIFEST="$BACKUP_DIR/manifest.json"
if [[ ! -f "$MANIFEST" ]]; then
    echo "Missing manifest.json in $BACKUP_DIR" >&2
    exit 1
fi

ARTIFACT_NAME="$(python3 - <<'PY' "$MANIFEST"
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["artifact"])
PY
)"
if ! is_safe_manifest_artifact "$ARTIFACT_NAME"; then
    echo "Unsafe artifact path in manifest: $ARTIFACT_NAME" >&2
    exit 1
fi
ARTIFACT="$BACKUP_DIR/$ARTIFACT_NAME"

if [[ ! -f "$ARTIFACT" ]]; then
    echo "Artifact not found: $ARTIFACT" >&2
    exit 1
fi

BACKUP_DIR_REAL="$(cd "$BACKUP_DIR" && pwd -P)"
ARTIFACT_REAL="$(cd "$(dirname "$ARTIFACT")" && pwd -P)/$(basename "$ARTIFACT")"
if [[ "$ARTIFACT_REAL" != "$BACKUP_DIR_REAL/"* ]]; then
    echo "Artifact escapes backup directory: $ARTIFACT_NAME" >&2
    exit 1
fi

EXPECTED_SHA="$(python3 - <<'PY' "$MANIFEST"
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["sha256"])
PY
)"
ACTUAL_SHA="$(sha256sum "$ARTIFACT" | awk '{print $1}')"

if [[ "$EXPECTED_SHA" != "$ACTUAL_SHA" ]]; then
    echo "Checksum mismatch for $ARTIFACT" >&2
    exit 1
fi

if [[ "$ARTIFACT" == *.pgdump ]]; then
    require_command pg_restore
    pg_restore --list "$ARTIFACT" >/dev/null
    echo "pg_restore --list OK: $ARTIFACT"
fi

if [[ "$ARTIFACT" == *.tar.gz ]]; then
    tar -tzf "$ARTIFACT" >/dev/null
    echo "tar test OK: $ARTIFACT"
fi

echo "Backup verified: $BACKUP_DIR"
