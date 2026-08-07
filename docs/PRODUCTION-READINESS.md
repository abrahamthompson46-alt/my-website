# Production Readiness — Zreta Marketing Platform

Run before every production deploy:

```bash
python manage.py check
python manage.py check_production
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_roles
```

---

## Owner / staff workflows

| Task | Where |
|------|--------|
| Add or edit a product (name, copy, hero image, publish) | **Control Room → Products** (`/control/products/`) |
| Track demos & subscriptions per product | **Control Room → Products → Manage** (product detail page) |
| Update demo request status | **Ops → Demo Requests** (`/ops/demo-requests/`) |
| View revenue, customers, analytics | **Ops Dashboard** (`/ops/`) |
| Site colors & branding | **Control Room → Settings** |
| Bootstrap content & seeds | **Control Room → Platform Setup** |

Staff must enable **two-factor authentication (MFA)** before accessing any authenticated area.

---

## User accounts & security

| Feature | Status |
|---------|--------|
| Login / logout / password reset | Ready |
| Account lockout after failed attempts | Ready |
| Rate limiting on login | Ready |
| TOTP MFA + backup codes | Ready |
| Staff MFA required (all routes) | Ready |
| Email verification enforced on customer portal | Ready |
| Open redirect protection on login | Ready |
| CSRF on all forms | Ready |
| Security headers (CSP, HSTS in production) | Ready |
| Session tracking & revocation | Ready |
| Audit log (auth + demos + products) | Ready |

Public self-registration is controlled by **Platform Settings → Public registration enabled** (off by default for marketing launch).

---

## Demo request security

| Control | Detail |
|---------|--------|
| Honeypot field | Blocks basic bots |
| Rate limit | 5 submissions per IP per hour |
| Duplicate suppression | Same email + product within 24 hours rejected |
| Audit trail | Each submission logged in Activity Logs |
| CSRF | Required on homepage and product demo forms |

---

## Production environment checklist

- [ ] `DJANGO_DEBUG=False`
- [ ] `DJANGO_SECRET_KEY` — 50+ characters (run `deploy/scripts/generate-secret-key.sh`)
- [ ] `DJANGO_ALLOWED_HOSTS` — includes `zreta.com`, `www.zreta.com`
- [ ] `CSRF_TRUSTED_ORIGINS` — `https://zreta.com`, `https://www.zreta.com`
- [ ] PostgreSQL configured (`DB_*` vars)
- [ ] Redis running (`REDIS_URL=redis://127.0.0.1:6379/0`)
- [ ] Email backend configured (SMTP preferred; file backend OK for staging)
- [ ] `collectstatic` run with production settings
- [ ] Superuser created + MFA enrolled
- [ ] `python manage.py bootstrap-marketing` (or seed commands) run once
- [ ] `curl -I https://zreta.com` returns 200
- [ ] `https://app.zreta.com` still serves ChurchHub

---

## Post-deploy smoke test

1. Visit homepage — loads without 500
2. Submit demo form — success message, appears in `/ops/demo-requests/`
3. Log in as staff — MFA enrollment prompt if not set up
4. Control Room → Products → Add product → publish → visible on `/products/`
5. Customer portal login — unverified email redirects to verification prompt

---

## Known launch configuration

- Payments disabled (`MANUAL_PAYMENTS_ENABLED=False`) — enable when gateways are configured
- File-based email in env example — switch to SMTP before relying on password reset in production
