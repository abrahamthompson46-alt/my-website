# Zreta — Current Production Truth

**Last verified:** 2026-08-13
**Repository HEAD:** `e2c7f4fec9796d77a5ad2a140aa838f6d5bd7fe3` (`e2c7f4f`)
**Status:** CURRENT PRODUCTION TRUTH — not the desired final architecture

This document records the **verified production VPS configuration** as discovered during the deployment architecture reconciliation audit. It exists to prevent accidental deployment against the wrong layout.

The **canonical repository architecture** (target state) is documented in `docs/ZRETA_DEPLOYMENT_PROCEDURE.md` and `docs/ZRETA_ARCHITECTURE_RECONCILIATION.md`. **Do not assume production matches the repo until reconciled.**

---

## Verified production facts (audit — 2026-08-13)

These items were verified during the repository-only audit. Re-confirm on the VPS before migration.

| Item | Current production value |
|------|--------------------------|
| **APP_DIR** | `/var/www/marketing-site` |
| **Linux service user** | `churchhub` |
| **Service group** | `www-data` |
| **Virtualenv** | `/var/www/marketing-site/venv` |
| **Gunicorn bind** | `127.0.0.1:8001` |
| **systemd service** | `marketing-site.service` |
| **PostgreSQL** | Version 16 cluster — online |
| **Git SHA on VPS** | `cbbbac919ed924d39fc1353d5bb5d3c0ae28b812` (`cbbbac9`) |
| **Commit message (VPS)** | Rebuild homepage around honest ChurchHub-first marketing |
| **Nginx** | Proxies public traffic to `127.0.0.1:8001` |
| **Health endpoint** | `https://www.zreta.com/health/` → HTTP 200 |
| **Private media** | `/media/private/` and `/media/payments/proofs/` → HTTP 404 |
| **Backup directory** | `/var/backups/zreta` — **does not exist** |
| **Backup scripts on VPS** | **Not present** (VPS checkout predates `5e99ed2`) |
| **Disk space** | ~66 GB free on `/var` filesystem |

---

## Canonical repository architecture (target — not yet applied to production)

| Item | Repository / docs expectation |
|------|-------------------------------|
| Linux user | `marketing` |
| Virtualenv | `/var/www/marketing-site/.venv` |
| Gunicorn bind | `unix:/run/zreta/gunicorn.sock` |
| Nginx upstream | `zreta_gunicorn` → Unix socket |
| systemd service | `marketing-site.service` (canonical unit in repo) |
| Deploy script | `deploy/scripts/deploy-app.sh` |

---

## Repository state vs production state

| Layer | Repository (`origin/main` @ `e2c7f4f`) | Production VPS |
|-------|----------------------------------------|----------------|
| Git SHA | `e2c7f4f` | `cbbbac9` |
| Linux user | `marketing` (canonical) | `churchhub` (verified) |
| Virtualenv | `.venv/` (canonical) | `venv/` (verified) |
| Gunicorn bind | Unix socket (canonical) | `127.0.0.1:8001` (verified) |
| Deploy guard | Present in `deploy-app.sh` | Not applicable until git pull |
| Backup scripts | In repo since `5e99ed2` | Not on VPS |
| Nginx marketing conf deny blocks | Pending in uncommitted prep | Unverified whether live nginx has equivalent blocks |

---

## Repository-only changes already pushed (`origin/main` @ `e2c7f4f`)

These are on `origin/main` but **not deployed to the VPS**:

| Change | Location |
|--------|----------|
| Deploy guard (`assert_canonical_deploy_allowed`) | `deploy/scripts/deploy-app.sh` |
| Zreta-first brand positioning + homepage tests | `website/`, `templates/`, `cms/` |

---

## Uncommitted reconciliation prep (working tree — not yet pushed)

The following changes are in the local working tree only:

| Change | Location |
|--------|----------|
| Private-media deny blocks in Certbot nginx conf | `deploy/nginx/zreta.com-marketing.conf` |
| Architecture reconciliation runbook | `docs/ZRETA_ARCHITECTURE_RECONCILIATION.md` |
| Production truth cross-references and state tables | This document |

---

## Production changes NOT yet performed

- Architecture reconciliation (`churchhub` → `marketing`, `venv/` → `.venv/`, `:8001` → socket)
- `git pull` / checkout of `e2c7f4f` on VPS
- Security commit deployment (`77fd427` through `e2c7f4f`)
- Database migrations from security stack on production
- Backup timer installation (`zreta-backup.service` / `zreta-backup.timer`)
- Nginx upstream cutover to `zreta_gunicorn` socket
- systemd unit replacement with canonical repo unit

---

## Deployment guard

`deploy/scripts/deploy-app.sh` refuses to run when it detects the production layout (`venv/` without `.venv/`, `User=churchhub`, or `:8001` bind in the installed systemd unit) unless:

```bash
export DEPLOY_ALLOW_CANONICAL=1
```

Use that override **only during a deliberate, operator-approved migration window** documented in `docs/ZRETA_ARCHITECTURE_RECONCILIATION.md`.

---

## Commits on `origin/main` not yet on production VPS

Production VPS is at `cbbbac9`. The following commits are in the repository but **not deployed**:

| SHA | Summary |
|-----|---------|
| `77fd427` | Phase 0 — billing/media hardening |
| `055a63f` | Phase 1A.1 — remove web-triggered deployment |
| `5e99ed2` | Phase 1A.2 — backup/DR foundation |
| `c63632b` | Fix python3 in backup restore scripts |
| `e2c7f4f` | Zreta-first brand positioning + deploy guard + production truth doc |

Target release SHA for next production deploy: **`e2c7f4f`** (after architecture reconciliation).

---

## Related documents

- `docs/ZRETA_ARCHITECTURE_RECONCILIATION.md` — migration concept, gates, rollback principles
- `docs/ZRETA_DEPLOYMENT_PROCEDURE.md` — canonical deploy flow (target architecture)
- `docs/ZRETA_BACKUP_IMPLEMENTATION.md` — backup scripts (require git update on VPS first)
- `docs/MIGRATION-ZRETA-SUBDOMAINS.md` — historical ChurchHub subdomain plan (partially stale for current production)
