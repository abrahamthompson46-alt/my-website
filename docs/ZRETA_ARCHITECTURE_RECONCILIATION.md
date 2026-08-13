# Zreta — Production Architecture Reconciliation

**Last updated:** 2026-08-13
**Repository HEAD:** `e2c7f4fec9796d77a5ad2a140aa838f6d5bd7fe3` (`e2c7f4f`)
**Status:** REPOSITORY PREPARATION — production migration **not yet performed**

This document describes how to reconcile the **verified production VPS layout** with the **canonical repository architecture**. It is an **infrastructure reconciliation**, not a ChurchHub-to-marketing content migration.

---

## What this is — and is not

| This document covers | This document does **not** cover |
|----------------------|----------------------------------|
| Linux user: `churchhub` → `marketing` | Moving ChurchHub off `zreta.com` (already done in production) |
| Virtualenv: `venv/` → `.venv/` | Replacing marketing content or CMS data |
| Gunicorn: `127.0.0.1:8001` → Unix socket | Running automated migration scripts (not yet approved) |
| Nginx upstream: TCP `:8001` → `zreta_gunicorn` socket | Greenfield deploy (`first-deploy-zreta.sh`, `setup-nginx-zreta.sh`) |
| systemd unit alignment with repo | Rewriting canonical architecture to match production ad-hoc layout |

Production **already serves the marketing Django application** on `zreta.com`. The mismatch is **how** it is deployed (user, venv path, bind address), not **what** is served.

---

## CURRENT production architecture (verified at audit time)

These facts were verified during the repository-only deployment audit on **2026-08-13**. Re-verify on the VPS before executing any migration step.

| Item | Verified production value |
|------|---------------------------|
| **APP_DIR** | `/var/www/marketing-site` |
| **Linux service user** | `churchhub` |
| **Service group** | `www-data` |
| **Virtualenv** | `/var/www/marketing-site/venv` |
| **Gunicorn bind** | `127.0.0.1:8001` |
| **systemd service** | `marketing-site.service` |
| **Nginx** | Proxies public traffic to `127.0.0.1:8001` |
| **Git SHA on VPS** | `cbbbac919ed924d39fc1353d5bb5d3c0ae28b812` (`cbbbac9`) |
| **Health endpoint** | `https://www.zreta.com/health/` → HTTP 200 |
| **Private media** | `/media/private/` and `/media/payments/proofs/` → HTTP 404 |
| **Backup directory** | `/var/backups/zreta` — did not exist at audit time |
| **Backup scripts on VPS** | Not present (VPS checkout predates `5e99ed2`) |

Items **not verified** during the audit (confirm in discovery): exact nginx config file path, SSL certificate paths, `DB_NAME` / `DB_USER` in production `.env`, whether `app.zreta.com` is configured.

---

## CANONICAL repository architecture (target)

Defined in `deploy/scripts/deploy-app.sh`, `deploy/systemd/marketing-site.service`, `deploy/gunicorn/gunicorn.conf.py`, and `deploy/nginx/zreta.com.conf`.

| Item | Canonical value |
|------|-----------------|
| **Linux user** | `marketing` |
| **Virtualenv** | `/var/www/marketing-site/.venv` |
| **Gunicorn bind** | `unix:/run/zreta/gunicorn.sock` |
| **Gunicorn config** | `deploy/gunicorn/gunicorn.conf.py` |
| **systemd service** | `marketing-site.service` (`RuntimeDirectory=zreta`, `Type=notify`) |
| **Nginx upstream** | `zreta_gunicorn` → `unix:/run/zreta/gunicorn.sock` |
| **Deploy entrypoint** | `deploy/scripts/deploy-app.sh` |

The Unix socket directory is created by systemd via `RuntimeDirectory=zreta` (mode `0750`). Gunicorn sets `umask = 0o007`, `user = marketing`, `group = www-data` so nginx (`www-data`) can connect.

---

## Why blindly running `deploy-app.sh` is dangerous

`deploy/scripts/deploy-app.sh` performs all of the following in one run:

1. Installs dependencies into `.venv` as user `marketing`
2. Runs `migrate` against the live PostgreSQL database
3. Regenerates `staticfiles/`
4. **Replaces** `/etc/systemd/system/marketing-site.service` with the canonical unit
5. **Restarts** Gunicorn on the Unix socket

If production has **not** been reconciled first:

| Failure mode | Consequence |
|--------------|-------------|
| systemd switches to socket bind while nginx still proxies to `:8001` | **Public site down** (502/connection refused) |
| Service runs as `marketing` but tree owned by `churchhub` | Permission errors, failed media writes |
| `.venv` missing but script assumes it | Failed pip install / gunicorn start |
| Migrations run while old code still serves public traffic | Schema/code mismatch during overlap window |

### Deployment guard (commit `e2c7f4f`)

`deploy-app.sh` includes `assert_canonical_deploy_allowed()` which **refuses to run** when it detects:

- `venv/` exists without `.venv/`
- systemd unit has `User=churchhub`
- systemd unit binds Gunicorn to `127.0.0.1:8001`

Override only during a deliberate, operator-approved migration window:

```bash
export DEPLOY_ALLOW_CANONICAL=1
sudo bash deploy/scripts/deploy-app.sh
```

See `docs/ZRETA_PRODUCTION_TRUTH.md` for current production vs repository state.

---

## Approved migration concept

High-level sequence. **No automated migration script exists yet** — operator executes each phase manually after review.

```
Backup → Discovery → Prepare marketing user → Create .venv →
Validate socket (parallel) → Install canonical systemd → Migrate/collectstatic →
Nginx cutover → Smoke test → Rollback window
```

Public traffic remains on `:8001` until the nginx cutover step. The socket backend is validated internally before any public routing change.

### Phase summary

| Phase | Goal | Public traffic affected? |
|-------|------|--------------------------|
| **R0 — Discovery** | Confirm audit facts; record nginx/systemd/.env paths | No |
| **R1 — Backup** | DB, media, `.env`, nginx, systemd unit | No |
| **R2 — Prepare `marketing` user** | Create user; set ownership on app tree | No |
| **R3 — Prepare `.venv`** | Fresh venv alongside legacy `venv/` | No |
| **R4 — Prepare Gunicorn/socket** | Manual or test daemon on socket | No |
| **R5 — Prepare systemd** | Install canonical unit file (defer restart) | No |
| **R6 — Validate backend** | Socket health = 200; public still via `:8001` | No |
| **R7 — Nginx + systemd cutover** | Switch upstream; restart canonical Gunicorn | **Yes** (seconds) |
| **R8 — Smoke test** | Public health, pages, private media 404 | Monitoring only |
| **R9 — Rollback** | Restore nginx + systemd to `:8001` layout | Yes (if invoked) |

### STOP / GATE points

**Do not proceed past a gate unless the check passes.**

| Gate | Required before next phase |
|------|---------------------------|
| **G0** (after R0) | Production layout documented; rollback paths identified; operator sign-off |
| **G1** (after R1) | Verified DB dump + media archive + nginx backup + `.env` copy exist |
| **G2** (after R3) | `.venv/bin/gunicorn` exists; legacy `venv/` preserved |
| **G3** (after R6) | `curl --unix-socket /run/zreta/gunicorn.sock … /health/` → 200 **and** public `https://www.zreta.com/health/` → 200 via `:8001` |
| **G4** (before R7) | `nginx -t` passes on edited config; socket Gunicorn confirmed healthy |
| **G5** (after R8) | All smoke tests pass for agreed rollback window (recommended: 15–30 minutes) |

**STOP immediately** if:

- Public health check fails at any point after R7
- `nginx -t` fails
- Gunicorn enters a crash loop after systemd restart
- Database migration errors occur

### Rollback principles

1. **Restore public routing first** — revert nginx to `:8001` upstream and reload.
2. **Restore process second** — reinstall backed-up systemd unit; restart Gunicorn on `:8001` / `churchhub` / `venv`.
3. **Database restore is last resort** — use `/var/backups/zreta/database/` only if migrations caused data corruption.
4. **Keep `venv/` until rollback window closes** — the legacy venv is the fastest rollback path for the application runtime.
5. **Do not delete backups** until migration is confirmed stable and a post-migration backup succeeds.

---

## PostgreSQL, media, and ownership notes

| Concern | Impact |
|---------|--------|
| **PostgreSQL** | Linux user change does **not** rename or recreate the database. Auth uses `DB_USER` / `DB_PASSWORD` from `.env`. Confirm credentials in R0. |
| **Migrations** | Required to deploy security commits (`77fd427`+). Run during R5/R6 before cutover; test socket backend before switching public traffic. |
| **Media / static ownership** | After R2, app tree should be `marketing:www-data`. Nginx reads via `www-data` group. Regenerate `staticfiles/` as `marketing` before cutover. |
| **Legacy `venv/`** | Do not delete until G5 passes. Rollback may depend on it. |

---

## Nginx cutover notes

Production likely uses **Certbot / Let's Encrypt** paths (not Cloudflare origin certs in `deploy/nginx/zreta.com.conf`).

For cutover, prefer `deploy/nginx/zreta.com-marketing.conf` (Certbot SSL paths, `zreta_gunicorn` upstream). The pending reconciliation prep commit adds nginx-level deny blocks for `/media/private/` and `/media/payments/proofs/` matching `deploy/nginx/zreta.com.conf` (not present at pushed HEAD `e2c7f4f`).

**Do not run** without adaptation:

- `deploy/scripts/setup-nginx-zreta.sh` (greenfield / Cloudflare certs)
- `deploy/scripts/first-deploy-zreta.sh` (full greenfield flow)
- `deploy/scripts/phase3-cutover-zreta-marketing.sh` (assumes ChurchHub-on-apex migration context)

---

## Backup layer (can install independently)

The backup scripts from commit `5e99ed2` do **not** depend on Gunicorn user, venv path, or nginx upstream. They can be installed before architecture reconciliation:

1. `git pull` / checkout target SHA (updates files on disk; does not restart Gunicorn)
2. `sudo bash deploy/scripts/backup-all.sh`
3. `sudo bash deploy/scripts/test-restore-drill.sh`
4. Install `zreta-backup.service` + `zreta-backup.timer`

See `docs/ZRETA_BACKUP_IMPLEMENTATION.md`.

---

## Repository-only changes (not yet on VPS)

### Already pushed (`e2c7f4f`)

| Change | File |
|--------|------|
| Deploy guard blocking unreconciled production layout | `deploy/scripts/deploy-app.sh` |

### Pending commit (working tree)

| Change | File |
|--------|------|
| Private-media deny blocks in Certbot marketing nginx conf | `deploy/nginx/zreta.com-marketing.conf` |
| Production truth + reconciliation documentation | `docs/ZRETA_PRODUCTION_TRUTH.md`, this document |

**Production changes NOT yet performed:** user migration, `.venv` creation, socket Gunicorn, nginx upstream cutover, systemd unit replacement, security commit deployment, backup timer installation.

---

## Related documents

| Document | Purpose |
|----------|---------|
| `docs/ZRETA_PRODUCTION_TRUTH.md` | Verified production facts vs canonical target |
| `docs/ZRETA_DEPLOYMENT_PROCEDURE.md` | Canonical deploy flow (target architecture) |
| `docs/ZRETA_BACKUP_IMPLEMENTATION.md` | Backup/restore scripts and timer install |
| `docs/MIGRATION-ZRETA-SUBDOMAINS.md` | Historical ChurchHub subdomain plan (partially stale for current production) |
| `docs/DEPLOYMENT-ZRETA-SAFE-PLAN.md` | Greenfield / shared-VPS safe deploy |
