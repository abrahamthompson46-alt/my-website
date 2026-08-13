# Zreta — Backup Policy

**Last updated:** 2026-08-13 (Phase 1A.2)  
**Scope:** VPS-hosted Zreta marketing site + customer portal (`zreta.com`)

---

## Purpose

Define what must be backed up, how often, and the recovery objectives for the current single-VPS architecture.

This policy supports the operational loop:

**BACKUP → VERIFY → RETAIN → RESTORE → VALIDATE**

---

## Architecture context

| Component | Production layout |
|-----------|-------------------|
| Application | `/var/www/marketing-site` (git checkout) |
| Database | PostgreSQL on same VPS (`127.0.0.1`) |
| Media | Local filesystem `/var/www/marketing-site/media/` |
| Cache/sessions | Redis (ephemeral — not backed up) |
| Static files | `staticfiles/` — regenerated via `collectstatic` |
| Secrets | `/var/www/marketing-site/.env` (not in git) |

---

## Recovery objectives (realistic for current scale)

| Metric | Target | Rationale |
|--------|--------|-----------|
| **RPO** (Recovery Point Objective) | **24 hours** (daily backup) | Single VPS; daily automated backup is practical without enterprise infrastructure |
| **RTO** (Recovery Time Objective) | **4 hours** | Manual VPS restore: provision, restore DB/media, redeploy app, validate |

These are operational targets, not contractual SLAs. Improve RPO/RTO when off-site replication or managed DB is introduced.

---

## What must be backed up

### 1. DATABASE — **Critical**

PostgreSQL database (`DB_NAME`, typically `marketing`).

Contains: users, subscriptions, invoices, payments, CMS content references, audit/control-room data.

**Method:** `pg_dump` custom format (`.pgdump`) via `deploy/scripts/backup-database.sh`.

**Not backed up by Django** — infrastructure-level job only.

### 2. MEDIA — **High priority (tiered)**

| Tier | Path | Priority | Notes |
|------|------|----------|-------|
| T1 | `media/private/payments/proofs/` | Critical | Payment proof documents (PII/financial evidence) |
| T2 | Other `media/` uploads | High | Customer/staff uploads, marketing assets |
| T3 | Regenerable assets | Low | Can often be re-seeded or re-uploaded |

**Method:** Full `media/` tar.gz via `deploy/scripts/backup-media.sh` (includes T1–T2; simplest consistent restore).

### 3. APPLICATION SOURCE — **Reconstructable**

Git repository on GitHub. Restore by checking out a **known commit SHA**, not by backing up the working tree as primary DR.

### 4. CONFIGURATION / SECRETS — **Documented, not committed**

| Item | Backup approach |
|------|-----------------|
| `.env` | Encrypted off-site copy or secrets manager; never git |
| Nginx configs | In repo under `deploy/nginx/` + `backup-nginx-config.sh` on VPS |
| TLS certificates | Cloudflare origin certs; secure offline copy |
| Cloudflare / DNS | Provider configuration (manual documentation) |
| Payment gateway keys | In `.env` / provider dashboards |

---

## Backup schedule

| Job | Frequency | Script |
|-----|-----------|--------|
| Database + media | Daily 02:30 UTC (timer) | `deploy/scripts/backup-all.sh` |
| Nginx (pre-change) | Ad hoc before migrations | `deploy/scripts/backup-nginx-config.sh` |

Automation: `deploy/systemd/zreta-backup.timer` + `zreta-backup.service`.

---

## Retention

Default policy (configurable via `deploy/env/backup.env.example`):

| Class | Retention |
|-------|-----------|
| Daily snapshots | **7** most recent per category (database, media) |
| Weekly | Covered by daily keep window (4 weeks ≈ 28 days not separately tiered in v1) |
| Monthly | Operator may archive one monthly copy off-site manually |

Pruning: `deploy/scripts/prune-backups.sh` (invoked by `backup-all.sh`).

**Disk full behavior:** prune runs after backup; if backup volume ≥ 90% full, script logs ERROR and exits non-zero.

---

## Storage location and permissions

| Path | Purpose |
|------|---------|
| `/var/backups/zreta/database/` | PostgreSQL dumps |
| `/var/backups/zreta/media/` | Media archives |
| `/var/log/zreta-backup/backup.log` | Backup job log |

- Filesystem mode: `700` on backup directories, `600` on artifacts
- Owner: root (backup jobs run as root via systemd)
- **Never** store backups under `/media/` or any web-served path
- **Never** commit backup files to git

---

## Verification

Each backup directory includes `manifest.json` with SHA-256 and size.

Post-backup verification (`deploy/scripts/verify-backup.sh`):

- Manifest checksum match
- Non-zero file size
- `pg_restore --list` for database dumps
- `tar -tzf` for media archives

---

## Failure detection

| Signal | Detection |
|--------|-----------|
| Backup job failed | Non-zero exit from `backup-all.sh`; systemd unit failure |
| Logs | `/var/log/zreta-backup/backup.log` |
| Stale backup | Absence of fresh timestamp under `/var/backups/zreta/database/` (> 36h) |
| Disk pressure | `prune-backups.sh` warns at ≥ 90% usage |

**Alerting (Phase 1A.2):** Documented only. Recommended: cron/systemd OnFailure email to operator, or external uptime monitor checking backup freshness.

---

## Security

Backup files contain customer and payment-related data.

- Restrict filesystem permissions
- Do not expose via Django or Nginx
- Do not include passwords in filenames or manifests
- Off-site copy recommended (encrypted object storage or SFTP to separate host)
- Encryption at rest: LUKS/disk encryption on VPS volume or gpg-encrypt archives for off-site transfer (operator choice)

---

## Restore testing

Minimum: quarterly **restore drill** on VPS/staging using `deploy/scripts/test-restore-drill.sh` into disposable database `zreta_restore_drill`.

Phase 1A.2 restore test status: see `docs/ZRETA_BACKUP_IMPLEMENTATION.md`.

---

## Related documents

- `docs/ZRETA_RESTORE_PROCEDURE.md` — full recovery runbook
- `docs/ZRETA_BACKUP_IMPLEMENTATION.md` — scripts and automation
- `docs/ZRETA_DEPLOYMENT_PROCEDURE.md` — normal releases
