# Production Go-Live Checklist — Zreta

Use this checklist before and after every production release.

## Pre-deploy (local / CI)

- [ ] `python manage.py check`
- [ ] `python manage.py check --deploy` (with production settings on staging)
- [ ] `python manage.py check_production`
- [ ] `python manage.py makemigrations --check`
- [ ] `python manage.py test`
- [ ] `python manage.py collectstatic --noinput` (staging/prod settings)

## VPS configuration

- [ ] `DJANGO_DEBUG=False`
- [ ] Strong `DJANGO_SECRET_KEY` (50+ characters)
- [ ] `DJANGO_ALLOWED_HOSTS` includes production domains
- [ ] `CSRF_TRUSTED_ORIGINS` includes HTTPS origins
- [ ] PostgreSQL configured (`DB_*`)
- [ ] `DB_SSLMODE` set appropriately for your Postgres topology
- [ ] `DB_STATEMENT_TIMEOUT_MS` set (default 30000)
- [ ] Redis running (`REDIS_URL`)
- [ ] SMTP configured (`EMAIL_*`)
- [ ] `SENTRY_DSN` configured (recommended)
- [ ] Nginx + Gunicorn + systemd applied from `deploy/`
- [ ] `python manage.py migrate --noinput`
- [ ] `python manage.py seed_roles`

## Backups and monitoring

- [ ] `zreta-backup.timer` enabled
- [ ] Off-site backup replication configured
- [ ] Cron or monitoring runs `python manage.py check_backup_freshness`
- [ ] Uptime monitor on `/` and `/health/`
- [ ] Quarterly restore drill documented

## Post-deploy smoke test

- [ ] Homepage loads over HTTPS
- [ ] Product page → start 30-day trial → register → portal dashboard
- [ ] Login + MFA for staff
- [ ] Checkout (sandbox) and webhook path
- [ ] Control Room: product media managers (screenshots, templates, videos)
- [ ] `/health/` returns `{"status":"ok"}` without internal error details

## Weekly owner review

- [ ] New trials and expiring trials
- [ ] Pending manual payments
- [ ] Failed webhooks / 5xx errors (Sentry)
- [ ] Backup freshness
- [ ] Platform owner accounts and MFA status
