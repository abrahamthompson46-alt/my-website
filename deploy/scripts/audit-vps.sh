#!/usr/bin/env bash
# Read-only VPS audit — safe to run before deploying zreta.com
# Usage: bash deploy/scripts/audit-vps.sh | tee ~/vps-audit-$(date +%F).txt
set -uo pipefail

section() {
    echo
    echo "================================================================================"
    echo " $1"
    echo "================================================================================"
}

warn() { echo "  [!] $*"; }
ok()   { echo "  [ok] $*"; }

section "System"
uname -a || true
if [[ -f /etc/os-release ]]; then cat /etc/os-release; fi
echo "  Disk:"
df -h / /var/www 2>/dev/null || df -h /
echo "  Memory:"
free -h 2>/dev/null || true

section "Listening ports (80/443/8000+)"
if command -v ss >/dev/null; then
    ss -tlnp | grep -E ':80 |:443 |:800[0-9] |:900[0-9] ' || echo "  (no matches or no permission for process names)"
else
    netstat -tlnp 2>/dev/null | grep -E ':80 |:443 |:800' || true
fi

section "Nginx — enabled sites"
if command -v nginx >/dev/null; then
    nginx -v 2>&1 || true
    echo "  sites-enabled:"
    ls -la /etc/nginx/sites-enabled/ 2>/dev/null || warn "no sites-enabled"
    echo
    echo "  server_name directives (existing vhosts):"
    grep -Rh "server_name" /etc/nginx/sites-enabled/ /etc/nginx/conf.d/ 2>/dev/null | sed 's/^/    /' || true
    echo
    if grep -Rqh "zreta.com" /etc/nginx/sites-enabled/ /etc/nginx/sites-available/ 2>/dev/null; then
        warn "zreta.com already referenced in nginx configs — review before adding"
    else
        ok "no existing zreta.com nginx config found"
    fi
    echo
    echo "  upstream blocks (name collisions matter):"
    grep -Rh "^upstream " /etc/nginx/sites-enabled/ /etc/nginx/conf.d/ 2>/dev/null | sed 's/^/    /' || true
else
    warn "nginx not installed"
fi

section "/var/www contents"
ls -la /var/www/ 2>/dev/null || warn "/var/www missing"

section "Existing Gunicorn / uWSGI / app services"
systemctl list-units --type=service --all 2>/dev/null \
    | grep -iE 'gunicorn|uwsgi|daphne|celery|zreta|marketing|church|erp|microfinance|website' \
    || echo "  (no obvious app services or insufficient permissions)"

section "Unix sockets in /run and /tmp"
ls -la /run/**/*.sock /run/*.sock /tmp/*.sock 2>/dev/null | head -30 || \
    find /run -maxdepth 3 -name '*.sock' 2>/dev/null | head -30 || true

section "PostgreSQL databases"
if command -v psql >/dev/null && id postgres &>/dev/null; then
    sudo -u postgres psql -c '\l' 2>/dev/null | sed 's/^/  /' || warn "cannot list databases"
    if sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='marketing_site'" 2>/dev/null | grep -q 1; then
        warn "database marketing_site already exists"
    else
        ok "database marketing_site not present (or cannot check)"
    fi
else
    warn "postgresql not available for audit"
fi

section "Redis"
if command -v redis-cli >/dev/null; then
    redis-cli ping 2>/dev/null || warn "redis not responding"
    redis-cli INFO memory 2>/dev/null | grep -E 'used_memory_human|connected_clients' | sed 's/^/  /' || true
else
    warn "redis-cli not found"
fi

section "App users"
getent passwd | grep -E 'marketing|zreta|www-data|deploy|church|erp' || true
if id marketing &>/dev/null; then
    warn "user 'marketing' already exists — verify it is not used by another app"
else
    ok "user 'marketing' not present"
fi

section "SSL certificates"
ls -la /etc/ssl/cloudflare/ 2>/dev/null || echo "  /etc/ssl/cloudflare/ not found"
ls -la /etc/letsencrypt/live/ 2>/dev/null || echo "  no Let's Encrypt certs found"

section "Cloudflare / domain conflict check"
echo "  Ensure zreta.com DNS A records point ONLY here if this is a new site."
echo "  Existing sites on this VPS should use different server_name values."
echo "  Nginx routes by Host header — zreta.com config will NOT affect other domains."

section "Safe deployment checklist"
cat <<'EOF'
  Before deploying zreta.com alongside existing apps:

  [ ] Run this audit and save output
  [ ] Confirm no nginx server_name already includes zreta.com
  [ ] Confirm upstream name 'zreta_gunicorn' is unused (our config uses this)
  [ ] Confirm /var/www/marketing-site is empty OR is the intended clone target
  [ ] Use provision-zreta-app-only.sh (NOT full provision-vps.sh) if nginx/pg/redis exist
  [ ] Do NOT delete /etc/nginx/sites-enabled/default unless it conflicts with zreta.com
  [ ] Use nginx -t before every reload
  [ ] Deploy during low traffic; keep rollback: disable sites-enabled/zreta.com symlink

EOF

section "Audit complete"
