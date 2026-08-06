#!/usr/bin/env bash
# Phase 2: Deploy marketing site sidecar — does NOT touch zreta.com nginx.
# ChurchHub remains on zreta.com until Phase 3 cutover.
#
# Usage: sudo bash deploy/scripts/phase2-deploy-marketing-sidecar.sh
set -euo pipefail

APP_DIR="/var/www/marketing-site"

if [[ "$(id -u)" -ne 0 ]]; then
    echo "Run as root."
    exit 1
fi

cd "$APP_DIR"

if [[ ! -f .env ]]; then
    echo "Configure .env from deploy/env/zreta.com.env.example first."
    exit 1
fi

bash deploy/scripts/provision-zreta-app-only.sh
bash deploy/scripts/deploy-app.sh
bash deploy/scripts/bootstrap-marketing.sh

echo
echo "==> Marketing app running (NOT yet on zreta.com public URL)"
echo "Verify via unix socket (no nginx change):"
echo "  curl --unix-socket /run/zreta/gunicorn.sock -H 'Host: zreta.com' http://127.0.0.1/health/"
echo
echo "Expected: {\"status\":\"ok\",...}"
echo
echo "Confirm zreta.com still serves ChurchHub:"
echo "  curl -sS -o /dev/null -w '%{http_code}\n' https://zreta.com/"
echo
echo "When both pass, proceed to Phase 3:"
echo "  sudo bash deploy/scripts/phase3-cutover-zreta-marketing.sh"
