# Safe deployment plan — zreta.com on shared VPS

**VPS:** `162.35.179.20` · **Domain:** `zreta.com` + `www.zreta.com`  
**Goal:** Add the marketing site **without disturbing existing applications**

> **Note:** Remote SSH audit from this environment was not possible (no VPS credentials). Run the audit script on the server and paste results if you want a reviewed go/no-go before deploy.

---

## How multi-site hosting works on your VPS

Nginx routes traffic by **`Host` header** (`server_name`). Each site is a separate config file:

```
Request: Host: existing-app.com  →  existing nginx vhost  →  existing gunicorn socket
Request: Host: zreta.com         →  zreta.com vhost         →  /run/zreta/gunicorn.sock
```

**zreta.com will not receive traffic meant for other domains**, as long as:

1. Each site has its own `server_name`
2. No two configs claim the same domain
3. You do **not** remove other sites from `sites-enabled`

---

## Risks in the original deploy scripts (fixed)

| Risk | Original behavior | Safe approach |
|------|-------------------|---------------|
| Removes default site | `rm sites-enabled/default` | **Removed** — other sites keep default/catch-all |
| Full VPS reprovision | `apt upgrade`, UFW force enable | Use **`provision-zreta-app-only.sh`** on shared VPS |
| Upstream name collision | `upstream marketing_gunicorn` | Renamed to **`zreta_gunicorn`** |
| Socket collision | `/run/marketing-site/*.sock` | Isolated to **`/run/zreta/gunicorn.sock`** |
| Overwrite `/var/www/*` | Blind clone | Audit directory first; clone only to `/var/www/marketing-site` |

---

## Phase 0 — Audit (required, read-only)

SSH into the VPS and run:

```bash
curl -sSL https://raw.githubusercontent.com/abrahamthompson46-alt/my-website/main/deploy/scripts/audit-vps.sh -o /tmp/audit-vps.sh
# OR after clone:
bash /var/www/marketing-site/deploy/scripts/audit-vps.sh | tee ~/vps-audit-$(date +%F).txt
```

### What to look for in audit output

| Check | Safe | Action if unsafe |
|-------|------|------------------|
| `server_name` already includes `zreta.com` | No match | Stop — resolve duplicate config first |
| `upstream zreta_gunicorn` exists | Not present | Stop — pick another upstream name |
| `/var/www/marketing-site` | Empty or this repo | Move/rename if another app lives there |
| Port 80/443 listeners | nginx only | Expected; nginx handles all HTTPS vhosts |
| DB `marketing_site` | Not exists | OK to create isolated DB |
| User `marketing` | Not exists OR dedicated to this app | Reuse only if unused |

**Save the audit file** before proceeding.

---

## Phase 1 — Isolation design for zreta.com

Everything for this app is **namespaced** so it won't collide with ChurchHub, ERP, or other apps on the same server:

| Resource | zreta.com value | Shared with other apps? |
|----------|-----------------|-------------------------|
| App directory | `/var/www/marketing-site` | No |
| Linux user | `marketing` | No (read-only to app) |
| systemd service | `marketing-site.service` | No |
| Gunicorn socket | `/run/zreta/gunicorn.sock` | No |
| Nginx upstream | `zreta_gunicorn` | No |
| Nginx vhost file | `sites-available/zreta.com` | No |
| PostgreSQL DB | `marketing_site` | No (separate DB, same PostgreSQL server) |
| Redis DB index | `0` (`redis://127.0.0.1:6379/0`) | **Shared instance** — use `/1` if index 0 is heavily used |

### Optional: dedicated Redis database index

If audit shows Redis is shared with other apps, set in `.env`:

```env
REDIS_URL=redis://127.0.0.1:6379/1
```

---

## Phase 2 — Cloudflare DNS (no impact on existing sites)

Add **only** zreta.com records:

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| A | `@` | `162.35.179.20` | Proxied |
| A | `www` | `162.35.179.20` | Proxied |

**Do not change DNS** for other domains pointing to this VPS.

---

## Phase 3 — Deploy (additive steps only)

### 3a. Clone to isolated directory

```bash
# Only if /var/www/marketing-site is empty or absent
sudo mkdir -p /var/www/marketing-site
sudo git clone https://github.com/abrahamthompson46-alt/my-website.git /var/www/marketing-site
```

If the directory already contains another project → **stop** and choose e.g. `/var/www/zreta-marketing` (update paths in `.env` and nginx `alias` lines accordingly).

### 3b. App-only provisioning (NOT full VPS provision)

```bash
cd /var/www/marketing-site
sudo bash deploy/scripts/provision-zreta-app-only.sh
```

**Do NOT run** `provision-vps.sh` on a VPS that already hosts other sites — it runs `apt upgrade` and may alter firewall rules.

### 3c. Environment

```bash
cp deploy/env/zreta.com.env.example .env
bash deploy/scripts/generate-secret-key.sh
nano .env   # DJANGO_SECRET_KEY + DB_PASSWORD
sudo chown marketing:www-data .env && sudo chmod 640 .env
```

### 3d. SSL (zreta.com only)

Cloudflare Origin Certificate → save as:

- `/etc/ssl/cloudflare/zreta.com.pem`
- `/etc/ssl/cloudflare/zreta.com.key`

Other sites' certificates are **untouched**.

### 3e. Deploy Gunicorn (isolated service)

```bash
sudo bash deploy/scripts/deploy-app.sh
sudo systemctl status marketing-site
curl --unix-socket /run/zreta/gunicorn.sock -H "Host: zreta.com" http://localhost/health/
```

### 3f. Enable Nginx vhost (additive)

```bash
sudo bash deploy/scripts/setup-nginx-zreta.sh
```

This script:

- Adds `sites-enabled/zreta.com` symlink
- Runs `nginx -t` before reload
- **Does not** delete `default` or other enabled sites

### 3g. Bootstrap content + admin

```bash
sudo bash deploy/scripts/bootstrap-marketing.sh
sudo -u marketing bash -c 'cd /var/www/marketing-site && source .venv/bin/activate && set -a && source .env && set +a && python manage.py createsuperuser'
```

---

## Phase 4 — Verification (existing + new)

```bash
# New site
curl -sS -o /dev/null -w "zreta.com: %{http_code}\n" https://www.zreta.com/
curl -sS https://www.zreta.com/health/

# Existing sites — replace with your real domains
curl -sS -o /dev/null -w "existing-app: %{http_code}\n" https://EXISTING-DOMAIN.example/
```

Browser: confirm existing apps still load, then test zreta.com.

---

## Rollback plan (under 2 minutes)

If zreta.com breaks nginx or affects other sites:

```bash
# 1. Disable zreta vhost only
sudo rm /etc/nginx/sites-enabled/zreta.com
sudo nginx -t && sudo systemctl reload nginx

# 2. Stop zreta gunicorn only
sudo systemctl stop marketing-site
sudo systemctl disable marketing-site
```

Existing sites continue using their own configs and services.

---

## Decision tree

```
VPS already has nginx + postgres + other sites?
├── YES → audit-vps.sh → provision-zreta-app-only.sh → deploy-app.sh → setup-nginx-zreta.sh
└── NO (blank VPS)  → provision-vps.sh → full DEPLOYMENT-ZRETA.md flow
```

---

## What I need from you before go-live

1. **Output of `audit-vps.sh`** — paste or attach `~/vps-audit-*.txt`
2. **List of existing domains** on this VPS (so we confirm no `server_name` overlap)
3. **Confirm `/var/www/marketing-site` is free** (or preferred alternate path)

Once you share the audit, we can give a explicit **go / no-go** before running deploy commands.

---

## Related files

| File | Purpose |
|------|---------|
| `deploy/scripts/audit-vps.sh` | Read-only VPS inventory |
| `deploy/scripts/provision-zreta-app-only.sh` | Additive app setup |
| `deploy/scripts/setup-nginx-zreta.sh` | Safe nginx enable |
| `deploy/nginx/zreta.com.conf` | Isolated vhost (`zreta_gunicorn`) |
| `deploy/env/zreta.com.env.example` | Production env template |
