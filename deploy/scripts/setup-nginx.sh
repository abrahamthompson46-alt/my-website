#!/usr/bin/env bash
# Install Nginx site config and reload.
# Usage: sudo DOMAIN=yourcompany.com bash deploy/scripts/setup-nginx.sh
set -euo pipefail

DOMAIN="${DOMAIN:-YOURDOMAIN.com}"
APP_DIR="/var/www/marketing-site"

if [[ "$(id -u)" -ne 0 ]]; then
    echo "Run as root."
    exit 1
fi

if [[ "$DOMAIN" == "YOURDOMAIN.com" ]]; then
    echo "Set your domain: sudo DOMAIN=yourcompany.com bash deploy/scripts/setup-nginx.sh"
    exit 1
fi

echo "==> Configuring Nginx for $DOMAIN and www.$DOMAIN ..."
cp "$APP_DIR/deploy/nginx/snippets/cloudflare-real-ip.conf" /etc/nginx/snippets/cloudflare-real-ip.conf
sed "s/YOURDOMAIN.com/${DOMAIN}/g" "$APP_DIR/deploy/nginx/marketing-site.conf" \
    > /etc/nginx/sites-available/marketing-site

ln -sf /etc/nginx/sites-available/marketing-site /etc/nginx/sites-enabled/marketing-site
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl reload nginx

echo "Nginx configured. Ensure SSL certs exist at:"
echo "  /etc/ssl/cloudflare/${DOMAIN}.pem"
echo "  /etc/ssl/cloudflare/${DOMAIN}.key"
