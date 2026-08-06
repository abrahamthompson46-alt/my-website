# Deploy the marketing website (VPS)

This guide deploys **only the public marketing site** in this repository — the Django app that showcases ChurchHub, Microfinance Core, and ERP Suite. It does **not** deploy those product applications themselves.

**Stack:** Ubuntu 24.04 · Nginx · Gunicorn · PostgreSQL · Redis · Cloudflare

---

## What you need before starting

| Item | Notes |
|------|--------|
| VPS | Ubuntu 24.04 with root/sudo SSH access |
| Domain | Apex + `www` (e.g. `yourcompany.com` and `www.yourcompany.com`) |
| Cloudflare | Domain added; DNS will point to VPS IP |
| Git or files | This repo on the server at `/var/www/marketing-site` |

**Email:** Production requires a non-console email backend. Until SMTP is ready, use the **file-based** backend in `deploy/env/production.vps.env.example` (emails saved to `logs/mail/`). Switch to SMTP before you need contact forms or password reset email.

---

## Architecture

```
Internet → Cloudflare (SSL edge) → Nginx :443 → Gunicorn (unix socket) → Django
                                         ↓
                              PostgreSQL + Redis (same VPS)
```

---

## Step 1 — Cloudflare DNS

1. Add an **A record** for `@` → your VPS public IP (**Proxied** / orange cloud).
2. Add an **A record** for `www` → same IP (**Proxied**).
3. SSL/TLS → set mode to **Full (strict)** (after origin cert is installed in Step 5).

---

## Step 2 — Upload the project to the VPS

```bash
# On the VPS (as root or with sudo)
sudo mkdir -p /var/www/marketing-site
sudo chown $USER:$USER /var/www/marketing-site

# Option A: git clone
git clone <YOUR_REPO_URL> /var/www/marketing-site

# Option B: rsync from your machine
rsync -avz --exclude .venv --exclude staticfiles --exclude .git \
  ./ user@YOUR_VPS_IP:/var/www/marketing-site/
```

---

## Step 3 — Provision the VPS (first time only)

```bash
cd /var/www/marketing-site
sudo bash deploy/scripts/provision-vps.sh
```

This installs Python, PostgreSQL, Redis, Nginx, creates the `marketing` system user, and creates the database. **Save the generated database password.**

---

## Step 4 — Configure environment

```bash
cd /var/www/marketing-site

# Generate a Django secret key
bash deploy/scripts/generate-secret-key.sh

# Create production .env
sudo cp deploy/env/production.vps.env.example .env
sudo nano .env   # fill in secret key, DB password, domain, company name
sudo chown marketing:www-data .env
sudo chmod 640 .env
```

Replace every `yourdomain.com` with your real domain. Set `SITE_URL` to your canonical URL (e.g. `https://www.yourdomain.com`).

---

## Step 5 — SSL (recommended: Cloudflare Origin Certificate)

Because DNS is proxied through Cloudflare, **Origin Certificates** are the simplest option:

1. Cloudflare Dashboard → **SSL/TLS** → **Origin Server** → **Create Certificate**
2. Hostnames: `yourdomain.com`, `*.yourdomain.com`
3. Save the certificate and private key on the VPS:

```bash
sudo mkdir -p /etc/ssl/cloudflare
sudo nano /etc/ssl/cloudflare/yourdomain.com.pem    # paste certificate
sudo nano /etc/ssl/cloudflare/yourdomain.com.key    # paste private key
sudo chmod 600 /etc/ssl/cloudflare/yourdomain.com.key
```

4. Cloudflare → SSL/TLS → **Full (strict)**

**Alternative:** Let's Encrypt with DNS challenge (Cloudflare API) if you prefer public CA certs on the origin.

---

## Step 6 — Deploy the application

```bash
cd /var/www/marketing-site
sudo chown -R marketing:www-data /var/www/marketing-site
sudo bash deploy/scripts/deploy-app.sh
```

This installs dependencies, runs migrations, collects static files, and starts the Gunicorn systemd service.

---

## Step 7 — Configure Nginx

```bash
sudo DOMAIN=yourdomain.com bash deploy/scripts/setup-nginx.sh
sudo nginx -t
sudo systemctl reload nginx
```

Ensure origin certificate paths in `/etc/nginx/sites-available/marketing-site` match your domain filenames.

---

## Step 8 — Bootstrap marketing content

```bash
sudo bash deploy/scripts/bootstrap-marketing.sh
```

Seeds roles, platform settings, **product catalog** (ChurchHub, Microfinance Core, ERP), CMS homepage, and blog content. Safe to re-run — existing data is skipped.

Create your staff account:

```bash
sudo -u marketing bash -c 'cd /var/www/marketing-site && source .venv/bin/activate && set -a && source .env && set +a && python manage.py createsuperuser'
```

---

## Step 9 — Verify production readiness

```bash
# On the VPS
curl -sS https://www.yourdomain.com/health/
# Expect: {"status":"ok","checks":{"database":"ok","cache":"ok","cache_backend":"redis",...}}

sudo systemctl status marketing-site
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis-server
```

**Browser checks:**

- [ ] Homepage loads over HTTPS
- [ ] `/products/` shows ChurchHub, Microfinance Core, ERP Suite
- [ ] `/contact/` form works (email goes to `logs/mail/` until SMTP is set)
- [ ] `/control/` — staff login + MFA for admin
- [ ] Static assets load (CSS, images)
- [ ] No mixed-content warnings

**Post-launch (Control Room `/control/`):**

- Update **Site Settings** → company name, branding, contact email
- Run any remaining seeds from **Platform Setup** if needed
- Enable MFA for all staff accounts

---

## Updating the site

```bash
cd /var/www/marketing-site
git pull   # or rsync new files
sudo bash deploy/scripts/deploy-app.sh
```

---

## Systemd & logs

| Service | Command |
|---------|---------|
| Restart app | `sudo systemctl restart marketing-site` |
| App logs | `sudo journalctl -u marketing-site -f` |
| Gunicorn access | `/var/log/marketing-site/gunicorn-access.log` |
| Nginx access | `/var/log/nginx/marketing-site.access.log` |
| Django logs | `/var/www/marketing-site/logs/django.log` |

---

## Cloudflare recommended settings

- **SSL/TLS:** Full (strict)
- **Always Use HTTPS:** On
- **Automatic HTTPS Rewrites:** On
- **Brotli:** On
- **Security → Settings:** sensible default (Medium or higher)

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| 502 Bad Gateway | `sudo systemctl status marketing-site` — check socket `/run/marketing-site/gunicorn.sock` |
| CSRF errors | Ensure `CSRF_TRUSTED_ORIGINS` includes `https://yourdomain.com` and `https://www.yourdomain.com` |
| Static files 404 | Re-run `collectstatic` via `deploy-app.sh` |
| Redis errors | `sudo systemctl status redis-server`; check `REDIS_URL=redis://127.0.0.1:6379/0` |
| Redirect loop | Cloudflare SSL must be **Full (strict)** with valid origin cert |
| `DisallowedHost` | Add domain to `DJANGO_ALLOWED_HOSTS` in `.env` |

---

## Files reference

```
deploy/
├── env/production.vps.env.example   # Production .env template
├── gunicorn/gunicorn.conf.py        # Gunicorn workers & socket
├── nginx/marketing-site.conf        # Nginx vhost (replace YOURDOMAIN.com)
├── nginx/snippets/cloudflare-real-ip.conf
├── scripts/
│   ├── provision-vps.sh             # First-time server setup
│   ├── deploy-app.sh                # Deploy / update app
│   ├── bootstrap-marketing.sh       # Seed marketing content
│   ├── setup-nginx.sh               # Install Nginx site
│   └── generate-secret-key.sh
└── systemd/marketing-site.service   # Gunicorn systemd unit
```

---

## When you're ready for SMTP

Edit `/var/www/marketing-site/.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.yourprovider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

Then: `sudo systemctl restart marketing-site`
