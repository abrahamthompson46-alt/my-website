# Zreta — Backup Implementation (Phase 1A.2)

**Last updated:** 2026-08-13  
**Status:** IN PROGRESS — restore drill not executed in Windows dev environment

---

## 1. Pre-implementation audit (existing capability)

| Capability | Status | Location |
|------------|--------|----------|
| PostgreSQL `pg_dump` automation | **Not found** | — |
| Media backup script | **Not found** | — |
| Restore script | **Not found** | — |
| Cron jobs for backup | **Not found** | — |
| systemd backup timer | **Not found** | — |
| Backup directory layout | **Not defined** | — |
| Nginx config backup | **Exists** | `deploy/scripts/backup-nginx-config.sh` → `/root/nginx-backups/` |
| Env file ad hoc backup | **Partial** | `fix-churchhub-env.sh` creates `.env.bak-*` |
| MFA backup codes | **Unrelated** | TOTP recovery codes in `accounts/` |
| Documented DB backup | **Partial** | FAQ/audit docs mention need; no automation |
| Cloud/object storage backup | **Not configured** | S3 optional for media only |
| Django-based backup | **Not present** | Correct — backups are infrastructure-level |

**Conclusion:** Only nginx configuration backup existed. No database or media DR foundation before Phase 1A.2.

---

## 2. New backup architecture

```
systemd timer (daily 02:30 UTC)
        ↓
deploy/scripts/backup-all.sh
        ├── backup-database.sh  → pg_dump -Fc → /var/backups/zreta/database/<stamp>/
        ├── backup-media.sh     → tar.gz     → /var/backups/zreta/media/<stamp>/
        ├── verify-backup.sh    → checksum + pg_restore --list / tar -t
        └── prune-backups.sh    → retention

Disaster recovery drill (VPS/staging):
        test-restore-drill.sh → restore-database.sh → disposable DB → SQL smoke → drop DB
```

---

## 3. Scripts added

| Script | Purpose |
|--------|---------|
| `deploy/scripts/lib/backup-common.sh` | Shared env loading, manifest, logging |
| `deploy/scripts/backup-database.sh` | PostgreSQL logical backup |
| `deploy/scripts/backup-media.sh` | Media tar.gz backup |
| `deploy/scripts/backup-all.sh` | Orchestrator |
| `deploy/scripts/verify-backup.sh` | Integrity verification |
| `deploy/scripts/prune-backups.sh` | Retention pruning |
| `deploy/scripts/restore-database.sh` | Restore to target DB (safety guards) |
| `deploy/scripts/test-restore-drill.sh` | Non-production DR drill |

---

## 4. Automation

| File | Purpose |
|------|---------|
| `deploy/systemd/zreta-backup.service` | oneshot backup unit |
| `deploy/systemd/zreta-backup.timer` | daily schedule |
| `deploy/env/backup.env.example` | Optional retention/path overrides |

**VPS install (documented, not executed from dev):**

```bash
sudo cp deploy/systemd/zreta-backup.service /etc/systemd/system/
sudo cp deploy/systemd/zreta-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now zreta-backup.timer
```

---

## 5. Python validation helpers

| Module | Purpose |
|--------|---------|
| `core/backup/manifest.py` | Manifest load/verify, path safety |
| `core/tests/test_backup_foundation.py` | Unit tests (no PostgreSQL required) |

---

## 6. Restore test status

| Environment | Result |
|-------------|--------|
| Windows dev (this session) | **NOT RUN** — `pg_dump` / `psql` not installed |
| VPS/staging | **Pending operator execution** of `test-restore-drill.sh` |

Phase 1A.2 is **not VERIFIED** until a successful restore drill is recorded on a system with PostgreSQL.

**To verify on VPS:**

```bash
sudo bash deploy/scripts/backup-database.sh
sudo bash deploy/scripts/test-restore-drill.sh
tail -20 /var/log/zreta-backup/backup.log
```

---

## 7. Security controls implemented

- Credentials read from `.env` at runtime; never written to manifests or filenames
- Backups stored outside web root (`/var/backups/zreta`)
- Restore refuses production DB without `RESTORE_ALLOW_PRODUCTION=1`
- `.gitignore` updated to exclude backup artifacts
- Django does not serve or manage backup files

---

## 8. Tests added

`core/tests/test_backup_foundation.py` (5 test methods):

- Safe backup root rejection (public media paths)
- Secret-like filename rejection
- Manifest checksum verification
- Checksum mismatch detection

Infrastructure scripts validated by structure review; full integration requires VPS PostgreSQL.

---

## 9. Files changed (Phase 1A.2)

**New:**

- `deploy/scripts/lib/backup-common.sh`
- `deploy/scripts/backup-*.sh`, `verify-backup.sh`, `restore-database.sh`, `prune-backups.sh`, `test-restore-drill.sh`
- `deploy/systemd/zreta-backup.service`, `zreta-backup.timer`
- `deploy/env/backup.env.example`
- `core/backup/manifest.py`, `core/backup/__init__.py`
- `core/tests/test_backup_foundation.py`
- `docs/ZRETA_BACKUP_POLICY.md`
- `docs/ZRETA_RESTORE_PROCEDURE.md`
- `docs/ZRETA_BACKUP_IMPLEMENTATION.md`

**Modified:**

- `.gitignore`
- `deploy/scripts/README.md`
- `docs/ZRETA_UPGRADE_PROGRESS.md`

---

## 10. Remaining risks

| Risk | Mitigation |
|------|------------|
| No off-site backup copy | Operator archives to separate storage (Phase 1+) |
| Restore drill not yet run on VPS | Required before marking VERIFIED |
| Single VPS single disk | RPO/RTO limited; document in policy |
| Redis sessions/cache not backed up | Users re-login after restore; acceptable |
| `.env` not auto-backed up | Operator encrypted backup documented |

---

## 11. Verification checklist

- [x] Scripts and documentation created
- [x] Python unit tests pass
- [x] Full Django test suite pass
- [ ] PostgreSQL restore drill executed on VPS/staging
- [ ] systemd timer installed on production VPS
