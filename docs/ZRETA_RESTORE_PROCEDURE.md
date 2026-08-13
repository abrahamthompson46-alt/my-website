# Zreta — Restore Procedure

**Last updated:** 2026-08-13 (Phase 1A.2)  
**Use when:** Database loss, media loss, VPS failure, or corrupted production data.

**Prerequisites:** Valid backup artifacts under `/var/backups/zreta/` (or off-site copy).

---

## Before you begin

1. **Stop writes** — enable maintenance mode or stop Gunicorn if continuing on same VPS.
2. **Record current state** — note commit SHA, backup timestamp chosen, incident time.
3. **Never restore over production** without explicit approval and a verified backup.

---

## 1. Obtain a known-good application version

```bash
cd /var/www/marketing-site
sudo -u marketing git fetch origin
sudo -u marketing git checkout <known-good-sha-or-tag>
sudo -u marketing git rev-parse HEAD   # record SHA
```

Application source can also be re-cloned from GitHub if the VPS is new.

---

## 2. Provision PostgreSQL

**Same VPS (database corrupted):** PostgreSQL service should already run.

**New VPS:** Run `deploy/scripts/provision-vps.sh` or `provision-zreta-app-only.sh`, then restore `.env`.

Verify:

```bash
sudo systemctl status postgresql
```

---

## 3. Restore database

Select backup directory, e.g. `/var/backups/zreta/database/20260813-023000`.

### Disaster recovery (production database)

```bash
cd /var/www/marketing-site
export RESTORE_ALLOW_PRODUCTION=1
export RESTORE_TARGET_DB=marketing   # must match DB_NAME in .env
sudo bash deploy/scripts/restore-database.sh /var/backups/zreta/database/YYYYMMDD-HHMMSS
```

**Warning:** This replaces the production database. Confirm backup verified first:

```bash
bash deploy/scripts/verify-backup.sh /var/backups/zreta/database/YYYYMMDD-HHMMSS
```

### Non-production drill (recommended practice)

```bash
export RESTORE_TARGET_DB=zreta_restore_drill
sudo bash deploy/scripts/test-restore-drill.sh
```

---

## 4. Restore media

```bash
BACKUP_DIR=/var/backups/zreta/media/YYYYMMDD-HHMMSS
ARCHIVE="$BACKUP_DIR/media-YYYYMMDD-HHMMSS.tar.gz"
bash deploy/scripts/verify-backup.sh "$BACKUP_DIR"

cd /var/www/marketing-site
sudo -u marketing tar -xzf "$ARCHIVE"
sudo chown -R marketing:www-data media
```

Verify private proofs exist:

```bash
ls -la /var/www/marketing-site/media/private/payments/proofs/ | head
```

---

## 5. Restore environment configuration

`.env` is **not** in git. Restore from:

- Encrypted operator backup, or
- Rebuild from `deploy/env/zreta.com.env.example` + recorded secrets

Required variables: see `deploy/env/zreta.com.env.example` (DB_*, DJANGO_SECRET_KEY, REDIS_URL, CSRF_TRUSTED_ORIGINS, etc.).

```bash
chmod 640 /var/www/marketing-site/.env
chown marketing:www-data /var/www/marketing-site/.env
```

---

## 6. Run Django checks

```bash
cd /var/www/marketing-site
sudo -u marketing bash -c '
  set -a; source .env; set +a
  source .venv/bin/activate
  python manage.py check
  python manage.py check --deploy
'
```

---

## 7. Run migrations carefully

After a point-in-time restore, migrations should match backup age. Run:

```bash
python manage.py showmigrations
python manage.py migrate --plan
python manage.py migrate --noinput
```

If migration history conflicts with restored data, **stop** and assess — do not blindly migrate forward on unknown state.

---

## 8. Collect static files

```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
python manage.py collectstatic --noinput
```

---

## 9. Start Gunicorn

```bash
sudo systemctl restart marketing-site
sudo systemctl status marketing-site
```

---

## 10. Validate application

```bash
curl -sS -o /dev/null -w "HTTP %{http_code}\n" https://www.zreta.com/health/
```

Manual checks:

- Homepage loads
- Customer login works
- Sample invoice/payment records visible in admin or portal
- Staff Control Room accessible (MFA)

---

## 11. Validate payment and customer data

- Open a known user account (test credentials)
- Verify recent payment records and amounts match expectations
- Confirm invoice statuses reasonable for backup age

---

## 12. Validate private media access

- Confirm `/media/private/` returns 404 at Nginx (not publicly served)
- Log in as payment owner; download proof via `/app/payments/<uuid>/proof/`
- Confirm cross-user access still denied

---

## Rollback considerations

| Scenario | Action |
|----------|--------|
| Restore made things worse | Restore **previous** backup snapshot if available |
| Migration applied after bad restore | Restore DB again from older backup; avoid forward migration until root cause known |
| Media partial restore | Re-extract full tar.gz; do not mix partial trees |
| Wrong commit deployed | `git checkout` previous SHA + redeploy (no DB change) |

Database migrations are **not** automatically reversed.

---

## Related documents

- `docs/ZRETA_BACKUP_POLICY.md`
- `docs/ZRETA_BACKUP_IMPLEMENTATION.md`
- `docs/ZRETA_DEPLOYMENT_PROCEDURE.md`
