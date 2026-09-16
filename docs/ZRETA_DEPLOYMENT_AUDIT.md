# Zreta Platform — Deployment Audit

**Audit date:** 2026-08-13  
**Scope:** Production configuration templates, Docker, Nginx, Gunicorn, systemd, CI/CD

---

## Deployment architecture

```
Internet → Cloudflare (TLS) → Nginx (443) → Gunicorn (unix socket) → Django
                                    ↓
                              staticfiles/ (alias)
                              media/ (alias — public)
PostgreSQL ← Django ORM
Redis ← cache + sessions
```

---

## Configuration audit

### DEBUG

| Environment | Setting | Status |
|-------------|---------|--------|
| Production | `DEBUG = False` hardcoded | ✅ |
| Production | Raises if weak SECRET_KEY | ✅ |
| Development | `DEBUG` from env, default False | ✅ |
| Test | `DEBUG = False` | ✅ |

### ALLOWED_HOSTS

| Finding | Severity | Detail |
|---------|----------|--------|
| Production requires non-localhost hosts | ✅ | `production.py:19-22` |
| Default dev allows localhost only | ✅ | `base.py:18` |

### CSRF_TRUSTED_ORIGINS

| Finding | Severity | Detail |
|---------|----------|--------|
| Required in production | ✅ | Raises if empty |
| Must include HTTPS origins | ✅ | Documented in `.env.production.example` |

### SECRET_KEY

| Finding | Severity | Detail |
|---------|----------|--------|
| Insecure defaults blocked in prod | ✅ | `_INSECURE_SECRET_KEYS` check + 50 char min |
| Dev default present | ⚠️ MEDIUM | Only safe if production settings always used on VPS |

### HTTPS / HSTS

| Control | Production | Nginx |
|---------|------------|-------|
| SECURE_SSL_REDIRECT | ✅ True | HTTP→HTTPS redirect |
| SECURE_PROXY_SSL_HEADER | ✅ | Cloudflare X-Forwarded-Proto |
| HSTS 1 year + subdomains + preload | ✅ | — |
| TLS 1.2/1.3 | — | ✅ nginx config |

### Secure cookies

| Cookie | Production |
|--------|------------|
| SESSION_COOKIE_SECURE | ✅ |
| CSRF_COOKIE_SECURE | ✅ |
| SESSION_COOKIE_HTTPONLY | ✅ |
| CSRF_COOKIE_HTTPONLY | ✅ |
| SameSite=Lax | ✅ |

### Database credentials

| Finding | Severity | Detail |
|---------|----------|--------|
| Credentials via env vars | ✅ | DB_* in settings |
| No SSL mode enforcement | ⚠️ MEDIUM | Add `sslmode=require` for managed Postgres |
| Docker default password `changeme` | ⚠️ LOW | Dev compose only |

### Redis

| Finding | Severity | Detail |
|---------|----------|--------|
| Required in production | ✅ | Startup fails without REDIS_URL |
| Used for cache + sessions | ✅ | `config/redis_settings.py` |
| systemd After=redis-server | ✅ | `marketing-site.service` |

### Nginx

| Finding | Severity | Location | Detail |
|---------|----------|----------|--------|
| Static alias with cache headers | ✅ | marketing-site.conf:64-68 | 30d immutable |
| Public media alias | ⚠️ HIGH | :72-77 | No auth on uploads |
| X-Frame-Options SAMEORIGIN | ⚠️ LOW | :53 | Conflicts with Django DENY |
| client_max_body_size 25M | ✅ | :58 | Upload limit |
| Health check no-cache | ✅ | :80-87 | |
| Cloudflare real IP snippet | ✅ | Included | |

### Gunicorn

File: `deploy/gunicorn/gunicorn.conf.py`

| Setting | Assessment |
|---------|------------|
| Unix socket binding | ✅ Standard VPS pattern |
| Worker count | Review against CPU (not audited at runtime) |
| Timeout | Present in nginx proxy (60s) |

### systemd

File: `deploy/systemd/marketing-site.service`

| Hardening | Status |
|-----------|--------|
| NoNewPrivileges | ✅ |
| PrivateTmp | ✅ |
| ProtectSystem=full | ✅ |
| ProtectHome | ✅ |
| ReadWritePaths limited | ✅ media, logs |
| Dedicated user `marketing` | ✅ |
| EnvironmentFile=.env | ✅ |
| Restart=on-failure | ✅ |

**Gap:** No explicit `WatchdogSec` or health-based restart.

### Firewall assumptions

Not defined in repo. Assumed:
- 443/80 public
- PostgreSQL/Redis localhost only

**Recommendation:** Document ufw rules in deployment guide.

### Backups

| Item | Status |
|------|--------|
| Automated pg_dump script | ❌ Not in repo |
| Media backup procedure | ❌ Not documented |
| Restore drill | ❌ Not documented |

### Logging

| Log | Location | Rotation |
|-----|----------|----------|
| django.log | logs/ | 10MB × 5 |
| error.log | logs/ | 10MB × 10 |
| security.log | logs/ | 10MB × 10 |
| nginx access/error | /var/log/nginx/ | OS default |

**Gap:** No centralized log aggregation configured (ELK, CloudWatch, etc.)

### Monitoring

| Tool | Status |
|------|--------|
| /health/ endpoint | ✅ DB + cache |
| Sentry | Optional via SENTRY_DSN |
| Uptime monitoring | ❌ Not in repo |
| Metrics (Prometheus) | ❌ Not in repo |

### Deployment rollback

| Mechanism | Status |
|-----------|--------|
| Git-based deploy via control room | ⚠️ Pull only, no automatic rollback |
| Blue/green or canary | ❌ |
| Database migration rollback plan | ❌ Not documented |
| systemd restart manual step | ⚠️ Required after deploy |

### CI/CD

File: `.github/workflows/ci.yml`

| Capability | Status |
|------------|--------|
| Test on push/PR | ✅ |
| Migration drift detection | ✅ |
| Deploy to production | ❌ Manual git pull on VPS |
| Secret scanning | ❌ Not in CI |
| Dependency vulnerability scan | ❌ Not in CI |

### Docker

| Component | Version |
|-----------|---------|
| Python | 3.12 |
| PostgreSQL | 16 |
| Redis | 7 |

Docker suitable for dev/staging; production docs focus on VPS + systemd.

---

## Production readiness checklist (from existing docs)

`docs/PRODUCTION-READINESS.md` provides operational checklist. Verified items align with codebase capabilities.

---

## Deployment risks summary

| Risk | Severity | Mitigation |
|------|----------|------------|
| Public media exposure | HIGH | Private storage + signed URLs |
| Manual deploy without rollback | MEDIUM | CI/CD with tagged releases |
| No backup automation | HIGH | Scheduled pg_dump + media sync |
| Web deploy triggers git pull | HIGH | Remove subprocess deploy |
| Redis single point of failure | MEDIUM | Redis persistence + monitoring |
| No DB SSL enforcement | MEDIUM | Add sslmode to DATABASES OPTIONS |

---

## Environment files

| File | Purpose |
|------|---------|
| `.env.example` | Development template |
| `.env.production.example` | Production template |
| `deploy/env/zreta.com.env.example` | Domain-specific example |

No secrets committed to repository ✅
