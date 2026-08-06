#!/usr/bin/env bash
# Bootstrap marketing content (products, CMS, blog) — safe to re-run (seeds skip if data exists).
# Run after first deploy: sudo bash deploy/scripts/bootstrap-marketing.sh
set -euo pipefail

APP_USER="marketing"
APP_DIR="/var/www/marketing-site"
VENV="$APP_DIR/.venv"

cd "$APP_DIR"

run_manage() {
    sudo -u "$APP_USER" bash -c "
        set -a
        source '$APP_DIR/.env'
        set +a
        source '$VENV/bin/activate'
        python manage.py $*
    "
}

echo "==> Seeding foundation..."
run_manage seed_roles
run_manage ensure_security_profiles
run_manage seed_control_room

echo "==> Seeding marketing content (products, CMS, blog)..."
run_manage seed_products
run_manage seed_cms
run_manage seed_marketing
run_manage seed_documentation

echo "==> Bootstrap complete."
echo "    Create a staff account: python manage.py createsuperuser"
echo "    Then sign in at /control/ to customize branding and content."
