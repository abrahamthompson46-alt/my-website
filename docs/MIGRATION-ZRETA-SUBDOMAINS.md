# Migration plan: zreta.com subdomain architecture

> **Get latest scripts:** `git pull origin main` in your clone before running migration steps.

**Current state (audit):**

| URL | Serves | Backend |
|-----|--------|---------|
| `zreta.com` / `www.zreta.com` | ChurchHub | `http://127.0.0.1:8000` |
| SSL | Certbot | `/etc/letsencrypt/live/zreta.com/` |

**Target state:**

| URL | Serves | Backend |
|-----|--------|---------|
| `zreta.com` / `www.zreta.com` | Marketing website | `unix:/run/zreta/gunicorn.sock` |
| `app.zreta.com` | ChurchHub | `http://127.0.0.1:8000` (unchanged process) |
| `finance.zreta.com` | Microfinance Core | future `:8002` |
| `erp.zreta.com` | Enterprise ERP | future `:8003` |

**Principle:** Migrate ChurchHub to `app.zreta.com` **first**, verify, then cut over the apex domain. ChurchHub code and deployment are **never overwritten**.

---

## Architecture diagram

```
                    ┌─────────────────────────────────────┐
                    │           Nginx (443/80)            │
                    └─────────────────────────────────────┘
                      │              │              │
         app.zreta.com│              │ zreta.com    │ (future subdomains)
                      ▼              ▼              ▼
              127.0.0.1:8000   /run/zreta/     127.0.0.1:8002+
              ChurchHub        gunicorn.sock    (not yet)
              (existing)       Marketing site
                               (new, isolated)
```

---

## DNS (Cloudflare or registrar)

Add before Phase 1:

| Type | Name | Content | Notes |
|------|------|---------|-------|
| A | `app` | `162.35.179.20` | ChurchHub subdomain |
| A | `@` | `162.35.179.20` | unchanged |
| A | `www` | `162.35.179.20` | unchanged |

Future (when apps deploy):

| Type | Name | Content |
|------|------|---------|
| A | `finance` | `162.35.179.20` |
| A | `erp` | `162.35.179.20` |

---

## Phase 0 — Backup (always)

```bash
cd /var/www/marketing-site   # after clone
sudo bash deploy/scripts/backup-nginx-config.sh
```

Backups go to `/root/nginx-backups/<timestamp>/`.

---

## Phase 1 — ChurchHub → `app.zreta.com` (apex unchanged)

**Goal:** ChurchHub accessible at `https://app.zreta.com` while `https://zreta.com` still serves ChurchHub.

### 1.1 Clone deployment repo (marketing configs only; does not touch ChurchHub)

```bash
sudo git clone https://github.com/abrahamthompson46-alt/my-website.git /var/www/marketing-site
```

### 1.2 Enable `app.zreta.com` nginx vhost

```bash
cd /var/www/marketing-site
sudo bash deploy/scripts/phase1-churchhub-app-subdomain.sh
```

Installs: `deploy/nginx/churchhub-app.zreta.com.conf` → proxies to `127.0.0.1:8000`.

### 1.3 SSL for `app.zreta.com` (Certbot)

**Option A — dedicated cert (simplest):**

```bash
sudo certbot --nginx -d app.zreta.com
```

**Option B — expand existing cert:**

```bash
sudo certbot --nginx --expand -d zreta.com -d www.zreta.com -d app.zreta.com
```

Certbot updates nginx SSL blocks automatically. Existing `zreta.com` certificate paths remain valid.

### 1.4 ChurchHub config (manual — in ChurchHub project, not this repo)

Add to ChurchHub environment/settings:

```env
ALLOWED_HOSTS=...,app.zreta.com
CSRF_TRUSTED_ORIGINS=https://app.zreta.com
```

Restart ChurchHub (same `:8000` process — no redeploy of marketing site).

### 1.5 Verification gate (must pass before Phase 2)

```bash
# New subdomain — must show ChurchHub
curl -sS -o /dev/null -w "app: %{http_code}\n" https://app.zreta.com/

# Apex — must STILL show ChurchHub
curl -sS -o /dev/null -w "apex: %{http_code}\n" https://zreta.com/
curl -sS -o /dev/null -w "www: %{http_code}\n" https://www.zreta.com/
```

Browser: log into ChurchHub at `https://app.zreta.com` and confirm full functionality.

**Do not proceed until app subdomain is verified.**

---

## Phase 2 — Deploy marketing site (sidecar; apex still ChurchHub)

**Goal:** Marketing app runs in isolation. Public `zreta.com` unchanged.

### 2.1 Configure marketing `.env`

```bash
cd /var/www/marketing-site
cp deploy/env/zreta.com.env.example .env
bash deploy/scripts/generate-secret-key.sh
nano .env   # DJANGO_SECRET_KEY, DB_PASSWORD
sudo chown marketing:www-data .env && sudo chmod 640 .env
```

### 2.2 Deploy marketing (no nginx change to zreta.com)

```bash
sudo bash deploy/scripts/phase2-deploy-marketing-sidecar.sh
```

Creates:

- PostgreSQL DB `marketing_site` (isolated)
- Gunicorn on `unix:/run/zreta/gunicorn.sock`
- systemd unit `marketing-site.service`

### 2.3 Verification gate (must pass before Phase 3)

```bash
# Marketing — internal only (unix socket)
curl --unix-socket /run/zreta/gunicorn.sock -H "Host: zreta.com" http://127.0.0.1/health/

# Public apex — still ChurchHub
curl -sS https://zreta.com/ | head -20   # should match ChurchHub, not marketing
curl -sS https://app.zreta.com/ | head -20
```

Create admin (optional before cutover):

```bash
sudo -u marketing bash -c 'cd /var/www/marketing-site && source .venv/bin/activate && set -a && source .env && set +a && python manage.py createsuperuser'
```

---

## Phase 3 — Cut over `zreta.com` to marketing

**Goal:** Swap apex nginx from `:8000` → marketing socket. `app.zreta.com` unchanged.

```bash
cd /var/www/marketing-site
sudo bash deploy/scripts/phase3-cutover-zreta-marketing.sh
```

This script:

1. Backs up current `zreta.com` nginx config to `/root/nginx-backups/zreta.com-churchhub-pre-cutover.conf`
2. Installs `deploy/nginx/zreta.com-marketing.conf`
3. Reuses existing Certbot cert at `/etc/letsencrypt/live/zreta.com/`
4. Prompts before `nginx reload`

### Verification after cutover

```bash
curl -sS https://www.zreta.com/health/          # marketing JSON health
curl -sS -o /dev/null -w "app: %{http_code}\n" https://app.zreta.com/   # ChurchHub
```

Browser:

- [ ] `https://zreta.com` → marketing homepage + products
- [ ] `https://app.zreta.com` → ChurchHub (unchanged)

---

## Rollback

### Rollback Phase 3 only (restore ChurchHub on apex)

```bash
sudo cp /root/nginx-backups/zreta.com-churchhub-pre-cutover.conf /etc/nginx/sites-available/zreta.com
sudo nginx -t && sudo systemctl reload nginx
```

Marketing Gunicorn can keep running; it just won't receive public apex traffic.

### Rollback Phase 1 (remove app subdomain)

```bash
sudo rm /etc/nginx/sites-enabled/churchhub-app.zreta.com
sudo nginx -t && sudo systemctl reload nginx
```

---

## Files reference

| File | Phase | Purpose |
|------|-------|---------|
| `deploy/nginx/churchhub-app.zreta.com.conf` | 1 | `app.zreta.com` → `:8000` |
| `deploy/nginx/zreta.com-marketing.conf` | 3 | `zreta.com` → marketing socket |
| `deploy/nginx/zreta-subdomains-future.conf.example` | future | finance / erp stubs |
| `deploy/scripts/phase1-churchhub-app-subdomain.sh` | 1 | Enable app vhost + certbot hints |
| `deploy/scripts/phase2-deploy-marketing-sidecar.sh` | 2 | Deploy marketing without apex change |
| `deploy/scripts/phase3-cutover-zreta-marketing.sh` | 3 | Swap apex to marketing |
| `deploy/scripts/backup-nginx-config.sh` | 0 | Pre-change backup |

---

## What we deliberately do NOT do

- Do not stop or replace ChurchHub on port `8000`
- Do not overwrite ChurchHub source or `/var/www/` churchhub directory
- Do not run `setup-nginx-zreta.sh` or `first-deploy-zreta.sh` (they target greenfield deploy)
- Do not remove Certbot certificates
- Do not change `zreta.com` nginx until Phase 3 verification passes

---

## Certbot renewal

After migration, Certbot auto-renewal continues for:

- `zreta.com` / `www.zreta.com` (marketing vhost)
- `app.zreta.com` (ChurchHub vhost)

Test renewal:

```bash
sudo certbot renew --dry-run
```

---

## Next: future subdomains

When Microfinance Core and ERP deploy, use separate ports and enable blocks from `deploy/nginx/zreta-subdomains-future.conf.example`, then:

```bash
sudo certbot --nginx -d finance.zreta.com
sudo certbot --nginx -d erp.zreta.com
```
