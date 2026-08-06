#!/usr/bin/env bash
# Backup nginx configuration before migration steps.
# Usage: sudo bash deploy/scripts/backup-nginx-config.sh
set -euo pipefail

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="/root/nginx-backups/${STAMP}"

if [[ "$(id -u)" -ne 0 ]]; then
    echo "Run as root."
    exit 1
fi

mkdir -p "$BACKUP_DIR"
cp -a /etc/nginx/sites-available "$BACKUP_DIR/" 2>/dev/null || true
cp -a /etc/nginx/sites-enabled "$BACKUP_DIR/" 2>/dev/null || true
cp -a /etc/letsencrypt/renewal "$BACKUP_DIR/letsencrypt-renewal" 2>/dev/null || true
ls -la /etc/letsencrypt/live/ > "$BACKUP_DIR/letsencrypt-live-list.txt" 2>/dev/null || true

nginx -T > "$BACKUP_DIR/nginx-full-dump.conf" 2>/dev/null || true

echo "Nginx backup saved to: $BACKUP_DIR"
ls -la "$BACKUP_DIR"
