# Deployment scripts

Run from the repository root on the VPS (`/var/www/marketing-site`).

## ChurchHub → marketing migration (zreta.com)

Use when ChurchHub is live on `zreta.com` and you need `app.zreta.com` first.

| Script | Phase | Description |
|--------|-------|-------------|
| `backup-nginx-config.sh` | 0 | Backup nginx + cert paths before any change |
| `phase1-churchhub-app-subdomain.sh` | 1 | Add `app.zreta.com` → `127.0.0.1:8000` |
| `phase2-deploy-marketing-sidecar.sh` | 2 | Deploy marketing app (apex unchanged) |
| `phase3-cutover-zreta-marketing.sh` | 3 | Switch `zreta.com` to marketing |

Full guide: [docs/MIGRATION-ZRETA-SUBDOMAINS.md](../docs/MIGRATION-ZRETA-SUBDOMAINS.md)

```bash
git clone https://github.com/abrahamthompson46-alt/my-website.git /var/www/marketing-site
cd /var/www/marketing-site
sudo bash deploy/scripts/phase1-churchhub-app-subdomain.sh
# ... certbot, verify ...
sudo bash deploy/scripts/phase2-deploy-marketing-sidecar.sh
sudo bash deploy/scripts/phase3-cutover-zreta-marketing.sh
```

## General deployment

| Script | Description |
|--------|-------------|
| `audit-vps.sh` | Read-only VPS inventory |
| `provision-vps.sh` | Full server setup (blank VPS only) |
| `provision-zreta-app-only.sh` | Additive app setup (shared VPS) |
| `deploy-app.sh` | Migrate, collectstatic, restart Gunicorn |
| `bootstrap-marketing.sh` | Seed marketing content |
| `setup-nginx-zreta.sh` | Greenfield nginx only (blocks if :8000 exists) |
| `generate-secret-key.sh` | Print Django secret key |

## Backup & disaster recovery (Phase 1A.2)

| Script | Description |
|--------|-------------|
| `backup-database.sh` | PostgreSQL `pg_dump` (custom format) |
| `backup-media.sh` | Tar.gz of `media/` |
| `backup-all.sh` | Database + media + verify + prune |
| `verify-backup.sh` | Checksum + `pg_restore --list` / tar test |
| `restore-database.sh` | Restore to disposable or production DB |
| `prune-backups.sh` | Retention cleanup |
| `test-restore-drill.sh` | Non-production restore validation |

Policy: [docs/ZRETA_BACKUP_POLICY.md](../../docs/ZRETA_BACKUP_POLICY.md)

## Nginx configs (`deploy/nginx/`)

| File | Purpose |
|------|---------|
| `churchhub-app.zreta.com.conf` | Phase 1 — ChurchHub subdomain |
| `zreta.com-marketing.conf` | Phase 3 — marketing apex (Certbot SSL) |
| `zreta-subdomains-future.conf.example` | Future finance/erp stubs |
