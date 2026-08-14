# Backup and Disaster Recovery — Zreta Marketing Site

Operational guide for backup, verification, and non-production restore testing on the marketing site VPS.

**This document does not claim backups are disaster-proof.** A backup that has never been restored is only a theory. Run restore drills regularly.

---

## Scope

| Component | Backed up | Method |
|-----------|-----------|--------|
| PostgreSQL database | Yes | `pg_dump` custom format via `deploy/scripts/backup-database.sh` |
| Media uploads | Yes | `deploy/scripts/backup-media.sh` (tar archive) |
| Nginx site config | Optional | `deploy/scripts/backup-nginx-config.sh` |
| Application source | No (Git) | Redeploy from repository |
| `.env` secrets | No | Maintain operator-controlled secret store / runbook |
| Redis cache | No | Ephemeral; rebuilds on restart |
| TLS certificates | No (Certbot) | Re-issue via Certbot if needed |

---

## Locations and permissions

| Path | Purpose |
|------|---------|
| `/var/backups/zreta/` | Backup root (`database/`, `media/`, `manifests/`) |
| `/var/log/zreta-backup/backup.log` | Backup event log |
| `/var/www/marketing-site/.env` | DB credentials read by backup scripts (mode **640**, group `marketing-runtime`) |

Backup directories are created with mode **700** where possible. Dump files and manifests use mode **600**.

---

## Schedule and retention

**Timer:** `deploy/systemd/zreta-backup.timer` — daily at **02:30 UTC** (±15 min jitter).

**Orchestration:** `deploy/scripts/backup-all.sh` runs database + media backups, verifies latest artifacts, then prunes old copies.

**Default retention** (`deploy/scripts/prune-backups.sh`):

- Daily: keep **7** most recent per category
- Weekly/monthly tiers: configurable via `RETENTION_WEEKLY` / `RETENTION_MONTHLY` (defaults 4 / 3)

Success marker: `/var/backups/zreta/.last-success` (touched after a clean `backup-all` run).

---

## What each backup contains

### Database

- Format: PostgreSQL custom (`*.pgdump`)
- Manifest: JSON with SHA-256, size, timestamp, hostname (`write_manifest_json` in `deploy/scripts/lib/backup-common.sh`)
- **Does not include** `.env` contents; only the database logical dump

### Media

- Archive of `/var/www/marketing-site/media/` (public and private paths on disk)
- Private files remain in the archive; access control is enforced at application/nginx layers when serving

---

## Integrity verification

After each successful backup-all run:

```bash
sudo bash deploy/scripts/verify-backup.sh /var/backups/zreta/database/YYYYMMDD-HHMMSS
sudo bash deploy/scripts/verify-backup.sh /var/backups/zreta/media/YYYYMMDD-HHMMSS
```

Verification checks manifest presence, SHA-256 match, and non-zero artifact size.

---

## Restore procedure (production emergency)

**Do not run against production without explicit authorization and a maintenance window.**

1. Stop writes: `sudo systemctl stop marketing-site`
2. Restore database:
   ```bash
   sudo RESTORE_ALLOW_PRODUCTION=1 bash deploy/scripts/restore-database.sh /var/backups/zreta/database/YYYYMMDD-HHMMSS
   ```
3. Restore media if needed (extract archive to `/var/www/marketing-site/media/` with correct ownership)
4. Run migrations if deploying newer code: `sudo -u marketing bash -c 'source /var/www/marketing-site/.venv/bin/activate && source /var/www/marketing-site/.env && python manage.py migrate --noinput'`
5. Start service: `sudo systemctl start marketing-site`
6. Verify: `curl -sS https://www.zreta.com/health/`

`restore-database.sh` refuses production DB names unless `RESTORE_ALLOW_PRODUCTION=1` is set.

---

## Non-production restore drill (recommended monthly)

Use the disposable-database drill — **safe for production VPS** because it targets a separate DB name:

```bash
sudo bash deploy/scripts/test-restore-drill.sh
# Or a specific backup:
sudo bash deploy/scripts/test-restore-drill.sh /var/backups/zreta/database/YYYYMMDD-HHMMSS
```

Default target database: `zreta_restore_drill` (dropped on exit unless `RESTORE_DRILL_KEEP_DB=1`).

The drill:

1. Creates/restores into the disposable DB
2. Runs validation queries (`django_migrations`, `auth_user` counts)
3. Drops the disposable DB on exit

**Record drill results** in the operator runbook (date, backup used, pass/fail).

---

## Encryption and off-site strategy

| Item | Current status | Recommendation |
|------|----------------|----------------|
| At-rest on VPS | Filesystem permissions only | Enable LUKS/disk encryption at VPS provider if available |
| In transit to off-site | Not automated | Sync encrypted copies (e.g. `rclone` to S3/GCS with SSE, or restic) |
| Backup encryption | Not built into scripts | GPG-encrypt dumps before off-site copy, or use provider-side encryption |

**Off-site minimum:** replicate `/var/backups/zreta/` daily to a second region/account. Test off-site restore quarterly.

---

## Secrets in backups

- Database dumps contain user password hashes, MFA secrets metadata, and business data — treat as **confidential**
- Media archives may contain payment proof uploads under `media/payments/proofs/` — treat as **highly confidential**
- Never publish backup paths or manifests publicly
- Do not commit backup artifacts to Git

---

## Operational roles

| Role | Responsibility |
|------|----------------|
| Platform owner | Authorize production restores, review drill results |
| VPS operator | Monitor timer, disk space, log errors in `/var/log/zreta-backup/` |
| Deploy operator | Run `backup-all.sh` manually after major migrations if needed |

---

## Manual backup

```bash
sudo bash deploy/scripts/backup-all.sh
```

Check log:

```bash
sudo tail -50 /var/log/zreta-backup/backup.log
```

---

## Related files

- `deploy/scripts/backup-all.sh`
- `deploy/scripts/backup-database.sh`
- `deploy/scripts/backup-media.sh`
- `deploy/scripts/restore-database.sh`
- `deploy/scripts/test-restore-drill.sh`
- `deploy/scripts/verify-backup.sh`
- `deploy/systemd/zreta-backup.service`
- `deploy/systemd/zreta-backup.timer`
