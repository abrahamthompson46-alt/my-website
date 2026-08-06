#!/usr/bin/env bash
# Phase 1: Add app.zreta.com → ChurchHub (127.0.0.1:8000)
# Does NOT change zreta.com / www.zreta.com (ChurchHub stays live on apex).
#
# Prerequisites:
#   - DNS A record: app.zreta.com → 162.35.179.20
#   - ChurchHub running on 127.0.0.1:8000
#
# Usage: sudo bash deploy/scripts/phase1-churchhub-app-subdomain.sh
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/marketing-site}"
SITE_AVAILABLE="/etc/nginx/sites-available/churchhub-app.zreta.com"
SITE_ENABLED="/etc/nginx/sites-enabled/churchhub-app.zreta.com"

if [[ "$(id -u)" -ne 0 ]]; then
    echo "Run as root."
    exit 1
fi

if [[ ! -f "$APP_DIR/deploy/nginx/churchhub-app.zreta.com.conf" ]]; then
    echo "Missing deploy/nginx/churchhub-app.zreta.com.conf — clone repo first."
    exit 1
fi

mkdir -p /var/www/certbot

bash "$APP_DIR/deploy/scripts/backup-nginx-config.sh"

if grep -Rqh "server_name app.zreta.com" /etc/nginx/sites-enabled/ 2>/dev/null; then
    echo "app.zreta.com nginx config already enabled."
else
    cp "$APP_DIR/deploy/nginx/churchhub-app.zreta.com.conf" "$SITE_AVAILABLE"
    ln -sf "$SITE_AVAILABLE" "$SITE_ENABLED"
    echo "Installed churchhub-app.zreta.com vhost (HTTP only until certbot)."
fi

nginx -t
systemctl reload nginx

echo
echo "==> Obtain SSL for app.zreta.com (Certbot)"
echo "Run ONE of:"
echo "  sudo certbot --nginx -d app.zreta.com"
echo "  # OR expand existing cert:"
echo "  sudo certbot --nginx --expand -d zreta.com -d www.zreta.com -d app.zreta.com"
echo
echo "==> ChurchHub ALLOWED_HOSTS (manual — do not skip)"
echo "Add 'app.zreta.com' to ChurchHub's ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS, then restart ChurchHub."
echo
echo "==> Verify before Phase 2"
echo "  curl -sS -o /dev/null -w '%{http_code}\n' https://app.zreta.com/"
echo "  curl -sS -o /dev/null -w '%{http_code}\n' https://zreta.com/          # should still be ChurchHub"
echo "  curl -sS -o /dev/null -w '%{http_code}\n' https://www.zreta.com/        # should still be ChurchHub"
