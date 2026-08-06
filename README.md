# Enterprise Platform

Django enterprise marketing site with customer portal, payments, operations dashboard, and no-code platform control room.

## Quick start (development)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements/development.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

For shared cache, sessions, and rate limits locally, start Redis and set `REDIS_URL` in `.env` (included in `.env.example`):

```bash
docker compose up redis -d
```

Open http://localhost:8000 — sign in via `/accounts/login/` or bootstrap data from `/control/` → **Platform Setup**.

## Production deployment

**zreta.com with ChurchHub on apex:** [docs/MIGRATION-ZRETA-SUBDOMAINS.md](docs/MIGRATION-ZRETA-SUBDOMAINS.md)  
**General VPS guide:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) · [docs/DEPLOYMENT-ZRETA.md](docs/DEPLOYMENT-ZRETA.md)

### 1. Configure environment

Copy the production template and fill in real values:

```bash
copy .env.production.example .env
```

Required variables: `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, PostgreSQL credentials, `REDIS_URL`, and SMTP email settings.

### 2. Deploy with Docker

```bash
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

The app runs on port **8000**. Health check: `GET /health/`

### 3. Post-deploy checklist

- [ ] Point DNS to your server and configure TLS (nginx/Caddy in front of Gunicorn)
- [ ] Set `SITE_URL` and `CSRF_TRUSTED_ORIGINS` to your HTTPS domain
- [ ] Run platform seeds from **Super Dashboard → Platform Setup**
- [ ] Configure payment gateway keys and register webhook URLs with providers
- [ ] Enable MFA for all staff accounts
- [ ] Test login, logout, password reset, and a test payment
- [ ] Optional: set `SENTRY_DSN` for error monitoring
- [ ] Optional: configure `AWS_*` vars for S3 media storage

### Manual deployment (VPS — Nginx + Gunicorn)

See **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** for the general guide, or **[docs/DEPLOYMENT-ZRETA.md](docs/DEPLOYMENT-ZRETA.md)** for the zreta.com VPS (`162.35.179.20`).

Quick reference:

```bash
sudo bash deploy/scripts/provision-vps.sh      # first time only
sudo bash deploy/scripts/deploy-app.sh
sudo DOMAIN=yourdomain.com bash deploy/scripts/setup-nginx.sh
sudo bash deploy/scripts/bootstrap-marketing.sh
```

### Manual deployment (without Docker)

```bash
pip install -r requirements/production.txt
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

Place nginx (or similar) in front for TLS and proxy `X-Forwarded-Proto`.

## Key URLs

| URL | Purpose |
|-----|---------|
| `/` | Public marketing site |
| `/accounts/login/` | Customer & staff sign-in |
| `/app/` | Customer portal |
| `/control/` | Super Dashboard (staff) |
| `/ops/` | Operations dashboard (staff) |
| `/admin/` | Django model admin (redirects staff to `/control/`) |
| `/health/` | Load balancer readiness probe |

## Running tests

```bash
python manage.py test --settings=config.settings.test
python manage.py check --deploy --settings=config.settings.test
```

## Security notes

- Staff must enable MFA before accessing `/control/`, `/ops/`, or `/admin/`
- Logout requires POST (CSRF-protected forms in portal headers)
- Payment webhooks validate signatures, amounts, and currencies before fulfillment
- Production settings reject weak secrets, SQLite, console email, and missing Redis

## Project structure

- `config/` — Django settings and URLs
- `control_room/` — Platform administration control room
- `accounts/` — Authentication, MFA, audit logs
- `payments/` — Gateways, webhooks, billing sync
- `operations/` — Staff ops dashboard
- `templates/` — Shared UI templates
- `static/` — CSS, JS, images
