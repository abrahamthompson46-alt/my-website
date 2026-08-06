#!/usr/bin/env bash
# Deploy or update the marketing website on the VPS.
# Run from project root: sudo bash deploy/scripts/deploy-app.sh
set -euo pipefail

APP_USER="marketing"
APP_DIR="/var/www/marketing-site"
VENV="$APP_DIR/.venv"

if [[ "$(id -u)" -ne 0 ]]; then
    echo "Run as root: sudo bash deploy/scripts/deploy-app.sh"
    exit 1
fi

cd "$APP_DIR"

echo "==> Installing Python dependencies..."
sudo -u "$APP_USER" bash -c "
    test -d '$VENV' || python3 -m venv '$VENV'
    source '$VENV/bin/activate'
    pip install --upgrade pip wheel
    pip install -r requirements/production.txt
"

echo "==> Running Django checks..."
sudo -u "$APP_USER" bash -c "
    set -a
    source '$APP_DIR/.env'
    set +a
    source '$VENV/bin/activate'
    python manage.py check --deploy
"

echo "==> Applying migrations..."
sudo -u "$APP_USER" bash -c "
    set -a
    source '$APP_DIR/.env'
    set +a
    source '$VENV/bin/activate'
    python manage.py migrate --noinput
"

echo "==> Collecting static files..."
sudo -u "$APP_USER" bash -c "
    set -a
    source '$APP_DIR/.env'
    set +a
    source '$VENV/bin/activate'
    python manage.py collectstatic --noinput
"

echo "==> Installing systemd service..."
cp deploy/systemd/marketing-site.service /etc/systemd/system/marketing-site.service
systemctl daemon-reload
systemctl enable marketing-site

echo "==> Restarting Gunicorn..."
systemctl restart marketing-site
sleep 2
systemctl --no-pager status marketing-site

echo "==> Deployment complete."
echo "    Health: curl -sS http://127.0.0.1:8000/health/  (via unix socket use nginx)"
curl --unix-socket /run/zreta/gunicorn.sock -sS -o /dev/null -w "Gunicorn socket: HTTP %{http_code}\n" -H "Host: zreta.com" http://localhost/health/ || true
