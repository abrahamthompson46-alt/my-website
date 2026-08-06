#!/usr/bin/env bash
# Additive setup for zreta.com ONLY — does not install nginx/postgres/redis system-wide,
# does not run apt upgrade, does not modify UFW, does not remove other nginx sites.
#
# Usage (on VPS, after clone):
#   sudo bash deploy/scripts/provision-zreta-app-only.sh
set -euo pipefail

APP_USER="marketing"
APP_DIR="/var/www/marketing-site"
LOG_DIR="/var/log/marketing-site"

if [[ "$(id -u)" -ne 0 ]]; then
    echo "Run as root."
    exit 1
fi

echo "==> Checking prerequisites..."
for cmd in python3 psql redis-cli nginx; do
    if ! command -v "$cmd" >/dev/null; then
        echo "Missing: $cmd — install it first or use full provision-vps.sh on a fresh server."
        exit 1
    fi
done

if [[ -d "$APP_DIR" ]] && [[ "$(ls -A "$APP_DIR" 2>/dev/null | wc -l)" -gt 0 ]]; then
    if [[ ! -f "$APP_DIR/manage.py" ]]; then
        echo "ERROR: $APP_DIR exists but does not look like this Django project."
        echo "       Choose a different APP_DIR or move the existing content."
        exit 1
    fi
    echo "  App directory exists with manage.py — OK"
fi

echo "==> Creating isolated app user and directories (no overwrite of existing users)..."
if id "$APP_USER" &>/dev/null; then
    echo "  User $APP_USER already exists — reusing"
else
    useradd --system --no-create-home --shell /usr/sbin/nologin "$APP_USER"
fi

mkdir -p "$APP_DIR" "$LOG_DIR" /etc/ssl/cloudflare
mkdir -p "$APP_DIR/media" "$APP_DIR/logs" "$APP_DIR/logs/mail"
chown -R "$APP_USER:www-data" "$APP_DIR" "$LOG_DIR"
chmod -R 775 "$APP_DIR/media" "$APP_DIR/logs"

echo "==> Creating isolated PostgreSQL database (skip if exists)..."
DB_NAME="${DB_NAME:-marketing_site}"
DB_USER="${DB_USER:-marketing}"
DB_PASSWORD="${DB_PASSWORD:-}"

if sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then
    echo "  Database $DB_NAME already exists — leaving unchanged"
else
    if [[ -z "$DB_PASSWORD" ]]; then
        DB_PASSWORD="$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 32)"
        echo "  Generated DB password: $DB_PASSWORD"
    fi
    if ! sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
        sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    fi
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
fi

echo "==> Installing Cloudflare real-IP snippet (merge-safe)..."
if [[ -f "$APP_DIR/deploy/nginx/snippets/cloudflare-real-ip.conf" ]]; then
    cp "$APP_DIR/deploy/nginx/snippets/cloudflare-real-ip.conf" /etc/nginx/snippets/cloudflare-real-ip.conf
fi

cat <<EOF

================================================================================
 zreta.com app provisioning complete (existing sites untouched)
================================================================================

  App dir:  $APP_DIR
  App user: $APP_USER
  DB name:  $DB_NAME
  DB user:  $DB_USER
  Socket:   /run/zreta/gunicorn.sock  (isolated from other apps)

Next:
  1. Configure .env from deploy/env/zreta.com.env.example
  2. sudo bash deploy/scripts/deploy-app.sh
  3. sudo bash deploy/scripts/setup-nginx-zreta.sh

EOF
