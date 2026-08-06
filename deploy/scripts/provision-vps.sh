#!/usr/bin/env bash
# First-time VPS provisioning for Ubuntu 24.04
# Run as root: sudo bash deploy/scripts/provision-vps.sh
set -euo pipefail

APP_USER="marketing"
APP_DIR="/var/www/marketing-site"
LOG_DIR="/var/log/marketing-site"

echo "==> Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y

echo "==> Installing system dependencies..."
apt-get install -y \
    python3 python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib \
    redis-server \
    nginx \
    git curl ufw fail2ban \
    libpq-dev build-essential

echo "==> Creating application user and directories..."
id -u "$APP_USER" &>/dev/null || useradd --system --create-home --home-dir "$APP_DIR" --shell /usr/sbin/nologin "$APP_USER"
mkdir -p "$APP_DIR" "$LOG_DIR" /etc/ssl/cloudflare /var/www/certbot
mkdir -p "$APP_DIR/media" "$APP_DIR/logs" "$APP_DIR/logs/mail"
chown -R "$APP_USER:www-data" "$APP_DIR" "$LOG_DIR"
chmod -R 775 "$APP_DIR/media" "$APP_DIR/logs"

echo "==> Configuring PostgreSQL..."
DB_NAME="${DB_NAME:-marketing_site}"
DB_USER="${DB_USER:-marketing}"
DB_PASSWORD="${DB_PASSWORD:-}"

if [[ -z "$DB_PASSWORD" ]]; then
    DB_PASSWORD="$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 32)"
    echo "Generated DB password: $DB_PASSWORD"
    echo "(Save this — you'll need it for .env)"
fi

sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1 \
    || sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1 \
    || sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo "==> Enabling Redis..."
systemctl enable --now redis-server

echo "==> Installing Cloudflare real-IP snippet for Nginx (after app is cloned)..."
if [[ -f deploy/nginx/snippets/cloudflare-real-ip.conf ]]; then
    cp deploy/nginx/snippets/cloudflare-real-ip.conf /etc/nginx/snippets/cloudflare-real-ip.conf
else
    echo "    (Skip — run setup-nginx.sh after cloning the app)"
fi

echo "==> Configuring UFW firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "==> Enabling fail2ban..."
systemctl enable --now fail2ban

cat <<EOF

================================================================================
 VPS provisioning complete.
================================================================================

Database:
  DB_NAME=$DB_NAME
  DB_USER=$DB_USER
  DB_PASSWORD=$DB_PASSWORD
  DB_HOST=127.0.0.1

Next steps:
  1. Clone/upload the marketing site to $APP_DIR
  2. Copy deploy/env/production.vps.env.example to $APP_DIR/.env and fill in values
  3. Run: sudo bash deploy/scripts/deploy-app.sh
  4. Configure Nginx + SSL (see docs/DEPLOYMENT.md)
  5. Point Cloudflare DNS A records to this server's IP (proxied)

EOF
