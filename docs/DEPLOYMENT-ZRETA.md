# Deploy zreta.com — production runbook

> **ChurchHub already on zreta.com?** Use the phased migration: **[MIGRATION-ZRETA-SUBDOMAINS.md](MIGRATION-ZRETA-SUBDOMAINS.md)**  
> **Shared VPS (no ChurchHub on apex)?** See **[DEPLOYMENT-ZRETA-SAFE-PLAN.md](DEPLOYMENT-ZRETA-SAFE-PLAN.md)**

| Setting | Value |
|---------|--------|
| **Domain** | `zreta.com` + `www.zreta.com` |
| **VPS IP** | `162.35.179.20` |
| **Repository** | https://github.com/abrahamthompson46-alt/my-website.git |
| **App path** | `/var/www/marketing-site` |
| **Canonical URL** | `https://www.zreta.com` |

---

## 1. Cloudflare DNS (do this first)

In Cloudflare for **zreta.com**:

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| A | `@` | `162.35.179.20` | Proxied (orange) |
| A | `www` | `162.35.179.20` | Proxied (orange) |

After origin certificate is installed (step 4): **SSL/TLS → Full (strict)**

---

## 2. SSH into the VPS

```bash
ssh root@162.35.179.20
```

---

## 3. Clone the repository

```bash
apt-get update && apt-get install -y git
mkdir -p /var/www/marketing-site
git clone https://github.com/abrahamthompson46-alt/my-website.git /var/www/marketing-site
cd /var/www/marketing-site
```

---

## 4. Provision the server

**Blank VPS:**
```bash
sudo bash deploy/scripts/provision-vps.sh
```

**VPS with existing websites:**
```bash
sudo bash deploy/scripts/provision-zreta-app-only.sh
```

**Save the database password** if one is generated.

---

## 5. Configure production environment

```bash
cd /var/www/marketing-site

# Copy zreta.com-specific env template
cp deploy/env/zreta.com.env.example .env

# Generate and paste Django secret key
bash deploy/scripts/generate-secret-key.sh
nano .env
# Set DJANGO_SECRET_KEY=<generated value>
# Set DB_PASSWORD=<password from provision-vps.sh>

chown marketing:www-data .env
chmod 640 .env
```

---

## 6. Cloudflare Origin Certificate (SSL)

1. Cloudflare → **SSL/TLS** → **Origin Server** → **Create Certificate**
2. Hostnames: `zreta.com`, `*.zreta.com`
3. On the VPS:

```bash
mkdir -p /etc/ssl/cloudflare
nano /etc/ssl/cloudflare/zreta.com.pem    # paste certificate
nano /etc/ssl/cloudflare/zreta.com.key    # paste private key
chmod 600 /etc/ssl/cloudflare/zreta.com.key
```

4. Cloudflare → SSL/TLS → **Full (strict)**

---

## 7. Deploy application (Gunicorn + systemd)

```bash
cd /var/www/marketing-site
chown -R marketing:www-data /var/www/marketing-site
sudo bash deploy/scripts/deploy-app.sh
```

Verify Gunicorn:

```bash
sudo systemctl status marketing-site
curl --unix-socket /run/zreta/gunicorn.sock -H "Host: zreta.com" http://localhost/health/
```

---

## 8. Configure Nginx

```bash
cd /var/www/marketing-site
sudo bash deploy/scripts/setup-nginx-zreta.sh
```

This adds `zreta.com` alongside existing nginx sites without removing them.

---

## 9. Bootstrap marketing content

```bash
sudo bash deploy/scripts/bootstrap-marketing.sh
```

Create staff admin:

```bash
sudo -u marketing bash -c '
  cd /var/www/marketing-site
  source .venv/bin/activate
  set -a && source .env && set +a
  python manage.py createsuperuser
'
```

---

## 10. Verify live site

```bash
curl -sS https://www.zreta.com/health/
curl -sS -o /dev/null -w "%{http_code}\n" https://www.zreta.com/
curl -sS -o /dev/null -w "%{http_code}\n" https://www.zreta.com/products/
```

**Browser checklist:**

- [ ] https://zreta.com loads
- [ ] https://www.zreta.com loads
- [ ] `/products/` shows ChurchHub, Microfinance Core, ERP Suite
- [ ] `/control/` staff login works
- [ ] HTTPS padlock valid (Cloudflare + origin cert)

---

## Updating after code changes

```bash
cd /var/www/marketing-site
git pull origin main
sudo bash deploy/scripts/deploy-app.sh
```

---

## Quick reference — services & logs

```bash
sudo systemctl restart marketing-site   # restart Gunicorn
sudo systemctl reload nginx             # reload Nginx
sudo journalctl -u marketing-site -f    # app logs
tail -f /var/log/nginx/zreta.com.access.log
```

---

## Files for this deployment

| File | Purpose |
|------|---------|
| `deploy/env/zreta.com.env.example` | Production `.env` template |
| `deploy/nginx/zreta.com.conf` | Nginx vhost |
| `deploy/systemd/marketing-site.service` | Gunicorn systemd unit |
| `deploy/gunicorn/gunicorn.conf.py` | Worker & socket settings |
