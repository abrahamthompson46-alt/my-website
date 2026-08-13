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

assert_canonical_deploy_allowed() {
    local reasons=()
    if [[ -d "$APP_DIR/venv" && ! -d "$APP_DIR/.venv" ]]; then
        reasons+=("virtualenv at $APP_DIR/venv (production layout; canonical expects $APP_DIR/.venv)")
    fi
    if [[ -f /etc/systemd/system/marketing-site.service ]]; then
        if grep -q '^User=churchhub' /etc/systemd/system/marketing-site.service 2>/dev/null; then
            reasons+=("systemd unit User=churchhub (canonical expects User=marketing)")
        fi
        if grep -qE '127\.0\.0\.1:8001|--bind 127\.0\.0\.1:8001' /etc/systemd/system/marketing-site.service 2>/dev/null; then
            reasons+=("systemd unit binds Gunicorn to 127.0.0.1:8001 (canonical expects unix:/run/zreta/gunicorn.sock)")
        fi
    fi
    if ((${#reasons[@]} > 0)) && [[ "${DEPLOY_ALLOW_CANONICAL:-0}" != "1" ]]; then
        echo "ERROR: Refusing canonical deploy-app.sh — production architecture not reconciled." >&2
        echo "" >&2
        echo "Detected:" >&2
        local reason
        for reason in "${reasons[@]}"; do
            echo "  - $reason" >&2
        done
        echo "" >&2
        echo "Production currently uses the churchhub/venv/8001 layout documented in" >&2
        echo "docs/ZRETA_PRODUCTION_TRUTH.md. Reconcile production deliberately before" >&2
        echo "running this script, or set DEPLOY_ALLOW_CANONICAL=1 only during a" >&2
        echo "controlled migration window." >&2
        exit 1
    fi
}

assert_canonical_deploy_allowed

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
    export DJANGO_SETTINGS_MODULE=config.settings.production
    source '$VENV/bin/activate'
    rm -rf '$APP_DIR/staticfiles'
    python manage.py collectstatic --noinput
    test -d '$APP_DIR/staticfiles/images' || (echo 'collectstatic failed' && exit 1)
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
