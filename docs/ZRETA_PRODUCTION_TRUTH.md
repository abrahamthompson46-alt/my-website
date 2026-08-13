# Zreta — Current Production Truth

**Last verified:** 2026-08-13
**Status:** CURRENT PRODUCTION TRUTH — not the desired final architecture

This document records the **verified production VPS configuration** as discovered during the deployment architecture reconciliation audit. It exists to prevent accidental deployment against the wrong layout.

The **canonical repository architecture** (target state) remains documented in `docs/ZRETA_DEPLOYMENT_PROCEDURE.md` and uses `marketing` user, `.venv`, and a Unix socket. **Do not assume production matches the repo until reconciled.**

---

## Verified production facts

| Item | Current production value |
|------|--------------------------|
| **APP_DIR** | `/var/www/marketing-site` |
| **Linux service user** | `churchhub` |
| **Service group** | `www-data` |
| **Virtualenv** | `/var/www/marketing-site/venv` |
| **Gunicorn bind** | `127.0.0.1:8001` |
| **systemd service** | `marketing-site.service` |
| **PostgreSQL** | Version 16 cluster — online |
| **Current Git SHA** | `cbbbac919ed924d39fc1353d5bb5d3c0ae28b812` (`cbbbac9`) |
| **Current commit message** | Rebuild homepage around honest ChurchHub-first marketing |
| **Nginx** | Proxies public traffic to the production Gunicorn configuration (`127.0.0.1:8001`) |
| **Health endpoint** | `https://www.zreta.com/health/` → HTTP 200 |
| **Private media** | `/media/private/` and `/media/payments/proofs/` → HTTP 404 |
| **Backup directory** | `/var/backups/zreta` — **does not exist** |
| **Backup scripts on disk** | **Not present** on current VPS checkout (older SHA) |
| **Backup scripts in repo** | Present from commit `5e99ed2` onward (not yet deployed to VPS) |
| **Disk space** | ~66 GB free on `/var` filesystem |

---

## Canonical repository architecture (target — not yet applied)

| Item | Repository / docs expectation |
|------|-------------------------------|
| Linux user | `marketing` |
| Virtualenv | `/var/www/marketing-site/.venv` |
| Gunicorn bind | `unix:/run/zreta/gunicorn.sock` |
| Nginx upstream | `zreta_gunicorn` → Unix socket |
| Deploy script | `deploy/scripts/deploy-app.sh` |

---

## Deployment guard

`deploy/scripts/deploy-app.sh` refuses to run when it detects the production layout (`venv/`, `User=churchhub`, or `:8001` bind in the installed systemd unit) unless:

```bash
export DEPLOY_ALLOW_CANONICAL=1
```

Use that override **only during a deliberate, operator-approved migration window.**

---

## Security commits not yet on production

Production is at `cbbbac9`. The following commits are on `origin/main` but **not deployed**:

| SHA | Summary |
|-----|---------|
| `77fd427` | Phase 0 — billing/media hardening |
| `055a63f` | Phase 1A.1 — remove web-triggered deployment |
| `5e99ed2` | Phase 1A.2 — backup/DR foundation |
| `c63632b` | Fix python3 in backup restore scripts |

Target release SHA: `c63632be5b03007c0896ba71cc16c46c031795ba`

---

## Related documents

- `docs/ZRETA_DEPLOYMENT_PROCEDURE.md` — canonical deploy flow (target architecture)
- `docs/ZRETA_BACKUP_IMPLEMENTATION.md` — backup scripts (require git update first)
- `docs/MIGRATION-ZRETA-SUBDOMAINS.md` — planned nginx/Gunicorn migration phases
