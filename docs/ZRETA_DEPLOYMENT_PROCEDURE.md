# Zreta — Controlled VPS Deployment Procedure

**Last updated:** 2026-08-13 (Phase 1A.1)  
**Purpose:** Replace the removed Control Room web deploy button with a safe, operator-controlled release flow.

The Django application **must not** perform deployment. All releases run on the VPS via SSH and the scripts in `deploy/scripts/`.

---

## Architecture

```
Developer workstation
    ↓ git commit / push
GitHub (origin)
    ↓ manual or CI-triggered fetch on VPS
VPS (/var/www/marketing-site)
    ↓ deploy/scripts/deploy-app.sh
PostgreSQL migrations + static files + Gunicorn restart
    ↓
Health check (/health/)
```

---

## Prerequisites

| Item | Location |
|------|----------|
| App directory | `/var/www/marketing-site` |
| App user | `marketing` |
| Environment file | `/var/www/marketing-site/.env` (from `deploy/env/zreta.com.env.example`) |
| Gunicorn service | `marketing-site` (see `deploy/systemd/marketing-site.service`) |
| Nginx config | `deploy/nginx/zreta.com.conf` or `deploy/nginx/marketing-site.conf` |

Full greenfield setup: [DEPLOYMENT-ZRETA.md](DEPLOYMENT-ZRETA.md)  
Script reference: [deploy/scripts/README.md](../deploy/scripts/README.md)

---

## Standard release (existing VPS)

Run on the VPS as **root** (or a user with sudo) after your commit is pushed to GitHub.

### 1. Developer — commit and push

```bash
# Local machine
python manage.py test
git push origin main
```

Record the commit SHA you intend to deploy.

### 2. Operator — SSH to VPS

```bash
ssh root@162.35.179.20
cd /var/www/marketing-site
```

### 3. Pull a known commit

```bash
sudo -u marketing git fetch origin
sudo -u marketing git checkout main
sudo -u marketing git pull origin main
sudo -u marketing git rev-parse HEAD   # verify SHA matches expected release
```

### 4. Run controlled deploy script

```bash
sudo bash deploy/scripts/deploy-app.sh
```

This script (as implemented today):

1. Installs/upgrades Python dependencies (`requirements/production.txt`)
2. Runs `python manage.py check --deploy`
3. Runs `python manage.py migrate --noinput`
4. Runs `python manage.py collectstatic --noinput`
5. Installs/refreshes the systemd unit
6. Restarts Gunicorn (`systemctl restart marketing-site`)

### 5. Validate and reload Nginx (required when config changed)

Whenever you deploy changes under `deploy/nginx/`, validate the active site configuration **before** reload:

```bash
sudo cp deploy/nginx/zreta.com.conf /etc/nginx/sites-available/zreta.com
sudo ln -sf /etc/nginx/sites-available/zreta.com /etc/nginx/sites-enabled/
sudo nginx -t
```

Only if `nginx -t` reports **syntax is ok** and **test is successful**:

```bash
sudo systemctl reload nginx
```

The production config must include private-media deny blocks (Phase 0):

- `location ^~ /media/private/` → deny all; return 404
- `location ^~ /media/payments/proofs/` → deny all; return 404

Public marketing media under other `/media/` paths (e.g. `products/screenshots/`) continues to be served by the general `/media/` alias block.

Do **not** skip validation. A syntax error leaves the previous Nginx config in effect only if you avoid reload after a failed test — always run `nginx -t` first.

### 6. Health check

```bash
curl -sS -o /dev/null -w "HTTP %{http_code}\n" https://www.zreta.com/health/
```

Or via the Gunicorn socket (see `deploy-app.sh`).

### 7. Smoke test

- Load homepage and customer login
- Verify `/app/payments/` checkout still works (staging/manual gateway if enabled)
- Check logs: `/var/log/nginx/` and `/var/www/marketing-site/logs/`

---

## Rollback

If a release fails after migrate:

```bash
cd /var/www/marketing-site
sudo -u marketing git log -5 --oneline
sudo -u marketing git checkout <previous-good-sha>
sudo bash deploy/scripts/deploy-app.sh
```

**Note:** Database migrations are not automatically reversed. If a migration was applied, you may need a forward fix or a planned DB restore from backup.

---

## First-time / provisioning

| Scenario | Script |
|----------|--------|
| Blank VPS | `deploy/scripts/provision-vps.sh` |
| Shared VPS (existing nginx/pg) | `deploy/scripts/provision-zreta-app-only.sh` |
| First zreta.com deploy | `deploy/scripts/first-deploy-zreta.sh` |

---

## What NOT to do

- Do **not** use Control Room → Platform Ops to deploy (web deploy removed in Phase 1A.1).
- Do **not** run `git pull` as the Gunicorn runtime user from a web request.
- Do **not** expose deployment webhooks that shell out to git or systemctl without strong authentication and review.

---

## Future (Phase 1+)

Optional improvements not implemented in Phase 1A.1:

- GitHub Actions CI on every push (test + lint)
- SSH-only deploy triggered manually or from Actions
- Staged releases with maintenance mode toggle
- Automated post-deploy health checks in CI

See `docs/ZRETA_UPGRADE_PROGRESS.md` for Phase 1 roadmap items.
