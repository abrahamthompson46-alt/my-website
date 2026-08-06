#!/usr/bin/env bash
# Phase 3: Switch zreta.com + www.zreta.com from ChurchHub (:8000) to marketing (unix socket).
# ONLY run after app.zreta.com verified and marketing socket health check passes.
#
# Usage: sudo bash deploy/scripts/phase3-cutover-zreta-marketing.sh
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/marketing-site}"
MARKETING_CONF="$APP_DIR/deploy/nginx/zreta.com-marketing.conf"
SITE_AVAILABLE="/etc/nginx/sites-available/zreta.com"
SITE_ENABLED="/etc/nginx/sites-enabled/zreta.com"
LEGACY_BACKUP="/root/nginx-backups/zreta.com-churchhub-pre-cutover.conf"

if [[ "$(id -u)" -ne 0 ]]; then
    echo "Run as root."
    exit 1
fi

echo "==> Pre-cutover checks"

if ! systemctl is-active --quiet marketing-site; then
    echo "ERROR: marketing-site (Gunicorn) is not running."
    exit 1
fi

HTTP_CODE="$(curl --unix-socket /run/zreta/gunicorn.sock -sS -o /dev/null -w '%{http_code}' -H 'Host: zreta.com' http://127.0.0.1/health/ || echo 000)"
if [[ "$HTTP_CODE" != "200" ]]; then
    echo "ERROR: Marketing health check failed (HTTP $HTTP_CODE). Aborting cutover."
    exit 1
fi
echo "  Marketing socket health: OK"

APP_CODE="$(curl -sS -o /dev/null -w '%{http_code}' https://app.zreta.com/ 2>/dev/null || echo 000)"
if [[ "$APP_CODE" != "200" && "$APP_CODE" != "302" && "$APP_CODE" != "301" ]]; then
    echo "WARNING: https://app.zreta.com returned HTTP $APP_CODE"
    echo "ChurchHub should be live on app.zreta.com before apex cutover."
    read -r -p "Continue anyway? [y/N] " ans
    [[ "$ans" =~ ^[Yy]$ ]] || exit 1
else
    echo "  app.zreta.com health: OK ($APP_CODE)"
fi

bash "$APP_DIR/deploy/scripts/backup-nginx-config.sh"

echo "==> Backing up current zreta.com nginx config"
if [[ -f "$SITE_AVAILABLE" ]]; then
    cp -a "$SITE_AVAILABLE" "$LEGACY_BACKUP"
    echo "  Saved: $LEGACY_BACKUP"
else
    # Find whichever file defines zreta.com
    FOUND="$(grep -Rl "server_name.*zreta.com" /etc/nginx/sites-enabled/ 2>/dev/null | grep -v churchhub-app | head -1 || true)"
    if [[ -n "$FOUND" ]]; then
        cp -a "$FOUND" "$LEGACY_BACKUP"
        echo "  Saved: $LEGACY_BACKUP (from $FOUND)"
    else
        echo "WARNING: Could not find existing zreta.com config to backup."
    fi
fi

echo "==> Installing marketing vhost for zreta.com"
cp "$MARKETING_CONF" "$SITE_AVAILABLE"
ln -sf "$SITE_AVAILABLE" "$SITE_ENABLED"

echo "==> Testing nginx config"
nginx -t

echo
echo "About to reload nginx:"
echo "  zreta.com / www.zreta.com  →  marketing site (unix:/run/zreta/gunicorn.sock)"
echo "  app.zreta.com              →  ChurchHub (127.0.0.1:8000) — unchanged"
read -r -p "Reload nginx now? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Aborted. Config copied but not reloaded."
    exit 0
fi

systemctl reload nginx

echo
echo "==> Cutover complete. Verify:"
echo "  curl -sS https://www.zreta.com/health/"
echo "  curl -sS -o /dev/null -w '%{http_code}\n' https://app.zreta.com/"
echo
echo "Rollback:"
echo "  sudo cp $LEGACY_BACKUP $SITE_AVAILABLE"
echo "  sudo nginx -t && sudo systemctl reload nginx"
