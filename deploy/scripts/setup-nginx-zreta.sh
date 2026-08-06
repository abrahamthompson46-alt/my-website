#!/usr/bin/env bash
# Safe Nginx install for zreta.com — does NOT remove other sites or default vhost.
# Run on VPS: sudo bash deploy/scripts/setup-nginx-zreta.sh
set -euo pipefail

APP_DIR="/var/www/marketing-site"
SITE_AVAILABLE="/etc/nginx/sites-available/zreta.com"
SITE_ENABLED="/etc/nginx/sites-enabled/zreta.com"

if [[ "$(id -u)" -ne 0 ]]; then
    echo "Run as root: sudo bash deploy/scripts/setup-nginx-zreta.sh"
    exit 1
fi

echo "==> Pre-flight checks..."

if grep -Rqh "server_name.*zreta.com" /etc/nginx/sites-enabled/ 2>/dev/null \
   && [[ ! -L "$SITE_ENABLED" ]]; then
    echo "ERROR: Another enabled nginx config already serves zreta.com."
    echo "       Inspect: grep -r zreta.com /etc/nginx/sites-enabled/"
    exit 1
fi

if grep -Rh "^upstream zreta_gunicorn" /etc/nginx/sites-enabled/ 2>/dev/null \
   | grep -qv "$SITE_AVAILABLE"; then
    echo "ERROR: upstream 'zreta_gunicorn' already defined elsewhere."
    exit 1
fi

if [[ ! -f /etc/ssl/cloudflare/zreta.com.pem ]] || [[ ! -f /etc/ssl/cloudflare/zreta.com.key ]]; then
    echo "WARNING: SSL certs missing at /etc/ssl/cloudflare/zreta.com.{pem,key}"
    echo "         nginx -t will fail until certs are installed."
fi

echo "==> Installing zreta.com vhost (additive)..."
cp "$APP_DIR/deploy/nginx/snippets/cloudflare-real-ip.conf" /etc/nginx/snippets/cloudflare-real-ip.conf
cp "$APP_DIR/deploy/nginx/zreta.com.conf" "$SITE_AVAILABLE"
ln -sf "$SITE_AVAILABLE" "$SITE_ENABLED"

echo "==> Current enabled sites (unchanged except zreta.com added):"
ls -la /etc/nginx/sites-enabled/

echo "==> Testing nginx config..."
nginx -t

echo "==> Reloading nginx (graceful — other vhosts stay active)..."
systemctl reload nginx

echo
echo "zreta.com nginx config enabled alongside existing sites."
echo "Default vhost and other server_name blocks were NOT removed."
