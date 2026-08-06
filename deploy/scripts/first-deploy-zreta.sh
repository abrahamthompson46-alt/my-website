#!/usr/bin/env bash
# First-time deployment for zreta.com on VPS 162.35.179.20
# Run on the VPS after cloning the repo and configuring .env + SSL certs.
#
# Prerequisites:
#   - .env configured from deploy/env/zreta.com.env.example
#   - Cloudflare origin cert at /etc/ssl/cloudflare/zreta.com.{pem,key}
#   - Cloudflare DNS A records pointing to 162.35.179.20
#
# Usage: sudo bash deploy/scripts/first-deploy-zreta.sh
#
# On a VPS with EXISTING websites, run audit first:
#   bash deploy/scripts/audit-vps.sh | tee ~/vps-audit.txt
# Use provision-zreta-app-only.sh instead of provision-vps.sh if nginx/pg already exist.
set -euo pipefail

APP_DIR="/var/www/marketing-site"
cd "$APP_DIR"

if [[ ! -f .env ]]; then
    echo "Missing .env — copy deploy/env/zreta.com.env.example and configure secrets first."
    exit 1
fi

if [[ ! -f /etc/ssl/cloudflare/zreta.com.pem ]] || [[ ! -f /etc/ssl/cloudflare/zreta.com.key ]]; then
    echo "Warning: SSL certs not found at /etc/ssl/cloudflare/zreta.com.{pem,key}"
    echo "Nginx will fail until Cloudflare origin certificate is installed."
    read -r -p "Continue anyway? [y/N] " ans
    [[ "$ans" =~ ^[Yy]$ ]] || exit 1
fi

chown -R marketing:www-data "$APP_DIR"
chmod 640 .env
chown marketing:www-data .env

bash deploy/scripts/deploy-app.sh
bash deploy/scripts/setup-nginx-zreta.sh
bash deploy/scripts/bootstrap-marketing.sh

cat <<'EOF'

================================================================================
 zreta.com first deploy complete
================================================================================

Create admin user:
  sudo -u marketing bash -c 'cd /var/www/marketing-site && source .venv/bin/activate && set -a && source .env && set +a && python manage.py createsuperuser'

Verify:
  curl -sS https://www.zreta.com/health/
  open https://www.zreta.com

Control room: https://www.zreta.com/control/

EOF
