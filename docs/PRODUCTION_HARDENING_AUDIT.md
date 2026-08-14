# Zreta Marketing Site — Production Hardening Audit (Phase 1)

**Audit date:** 2026-08-13  
**Repository HEAD:** `2b3160c09feda0112df05056def67b92172bed32` (`2b3160c`)  
**Scope:** Repository inspection + read-only production discovery (no modifications)  
**SOC 2:** Not in scope — audit notes sensible foundations only

---

## Executive summary

The Zreta marketing site has a **strong production Django baseline**: `DEBUG=False`, enforced secrets/hosts/CSRF, HTTPS/HSTS, Redis-backed sessions/cache/rate limits, CSP middleware, private payment-proof handling, webhook signature validation, and backup/restore scripts.

Production is **healthy and running** on the operator-intended runtime (`marketing` / `marketing-runtime` / `.venv` / `127.0.0.1:8001`), but the **repository deployment artifacts still describe a different canonical layout** (Unix socket / `www-data` group / `deploy/gunicorn/gunicorn.conf.py`). Live nginx remains a **minimal proxy** without static/media aliases or nginx-level private-media deny rules.

**Highest-priority application findings:**

1. **CRITICAL** — Invitation acceptance for an existing user logs in without password or MFA (`accounts/views.py`).
2. **HIGH** — MFA verify `?rescan=1` allows TOTP re-enrollment during login challenge, bypassing existing MFA if password step was completed (`accounts/views.py`).
3. **HIGH** — Most control-room and operations views are gated only by `is_staff`, not fine-grained RBAC.
4. **HIGH** — Repository vs production deployment drift (systemd, gunicorn bind, nginx hardening).

**Phase 1 rule:** No application or infrastructure code was modified during this audit.

---

## Verified production state (read-only, 2026-08-13)

These facts were observed on the VPS during read-only discovery **after** the earlier `churchhub`/`venv` reconciliation work.

| Item | Verified value |
|------|----------------|
| **Service** | `marketing-site.service` — **active** |
| **User / Group** | `marketing` / `marketing-runtime` |
| **Gunicorn** | `/var/www/marketing-site/.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8001` |
| **Git SHA** | `2b3160c` (matches `origin/main`) |
| **Public health** | `https://www.zreta.com/health/` → **200** |
| **`.env` permissions** | `churchhub:marketing-runtime` mode **640** |
| **Logs ownership** | `marketing:marketing-runtime` mode **775** |
| **Media ownership** | `churchhub:churchhub` mode **775** |
| **Legacy venv** | `/var/www/marketing-site/venv` still exists (`churchhub:churchhub`) |
| **Backups** | `/var/backups/zreta` and `/var/log/zreta-backup` **exist** (root-owned) |
| **Nginx** | `/etc/nginx/sites-available/zreta.com` → `proxy_pass http://127.0.0.1:8001` only |
| **TLS** | Certbot `/etc/letsencrypt/live/zreta.com/` |

**Not verified in this pass:** full `nginx -T` dump (sudo password required in batch SSH), PostgreSQL `SELECT version()` as postgres superuser, private-media HTTP response codes.

---

## Finding classification key

| Level | Meaning |
|-------|---------|
| **CRITICAL** | Exploitable path to account/data compromise or secret exposure |
| **HIGH** | Significant security or availability risk; fix before broad hardening sign-off |
| **MEDIUM** | Defense-in-depth gap or operational weakness |
| **LOW** | Minor hardening opportunity |
| **CLEAN** | Correctly implemented for current scale |

---

## 1. Django settings & environment loading

### CLEAN
- Production forces `DEBUG = False` (`config/settings/production.py`).
- Startup rejects weak/default `SECRET_KEY`, localhost-only `ALLOWED_HOSTS`, empty `CSRF_TRUSTED_ORIGINS`, SQLite, and console email backend.
- HTTPS redirect, secure session/CSRF cookies, HSTS (1 year, subdomains, preload), and `SECURE_PROXY_SSL_HEADER` configured for reverse-proxy deployment.
- WSGI/ASGI default to production settings (`config/wsgi.py`, `config/asgi.py`).
- `django_extensions` removed from production `INSTALLED_APPS`.
- Payment gateway credentials loaded from environment only (`config/settings/base.py`).

### HIGH
- **Repository deployment config ≠ live production config.** Repo `deploy/systemd/marketing-site.service` and `deploy/gunicorn/gunicorn.conf.py` assume Unix socket + `www-data` group. Live unit uses TCP `:8001`, `marketing-runtime`, and inline Gunicorn flags. Running `deploy-app.sh` without adaptation would be dangerous.

### MEDIUM
- `CSRF_TRUSTED_ORIGINS` validated for non-empty only, not for HTTPS-only entries (`production.py`).
- Staging settings lack HTTPS redirect/HSTS parity with production (`config/settings/staging.py`).
- CI runs `check --deploy` under test settings, not production settings (`.github/workflows/ci.yml`).
- Base settings include insecure default secret string; production rejects it, staging does not (`config/settings/base.py`).

### LOW
- Duplicate `.env` loading in `manage.py` and `config/env.py`.
- `SECURE_BROWSER_XSS_FILTER` is legacy; CSP is the meaningful control.

---

## 2. URL configuration & debug tooling

### CLEAN
- Debug Toolbar registered only when `DEBUG` is True (`config/urls.py`, `config/settings/development.py`).
- Test settings strip debug toolbar defensively (`config/settings/test.py`).
- Root URL routing cleanly separates public site, portals, control room, webhooks.

### MEDIUM
- `requirements.txt` (root) includes dev packages; production deploy path correctly uses `requirements/production.txt`, but any workflow installing root requirements would pull dev tools.

---

## 3. Authentication & account security

### CRITICAL
- **Existing-user invitation bypass:** `AcceptInvitationView` logs in an existing user when `accept_existing` is posted, with no password, existing session proof, or MFA step (`accounts/views.py` ~558–564). A leaked invite token grants account access.

### HIGH
- **MFA verify rescan during login:** `MFAVerifyView` accepts `?rescan=1` during pending MFA challenge and replaces enrolled TOTP after verifying a *new* secret (`accounts/views.py` ~241–266). Intended as device recovery, but allows MFA bypass after password authentication in the pending session. Tests explicitly cover this behavior (`accounts/tests/test_mfa.py`).
- **Client IP from `X-Forwarded-For` first hop** used for rate limits and audit (`accounts/services/rate_limit.py`). Spoofable unless nginx strips/forwards trusted headers only.
- **TOTP secrets stored plaintext** in database (`accounts/models/security.py`, `accounts/services/mfa.py`). DB read compromise exposes MFA factors.

### MEDIUM
- MFA disable/enroll endpoints lack dedicated throttling beyond password gate.
- Registration and invitation flows not rate-limited at view level.
- Standalone password-change URL uses Django default view, bypassing project audit flow (`accounts/urls.py`).

### CLEAN
- Login rate limiting, lockout settings, secure password hashers (Django defaults).
- CSRF middleware enabled globally.
- MFA enrollment/verify/rescan flows have automated tests.

---

## 4. Authorization & RBAC

### HIGH
- **Broad staff access:** Most control-room CRUD (products, pricing, CMS docs, settings, redirects, feature flags, seed commands) uses `ControlRoomMixin` → `is_staff` only (`control_room/views.py`, `control_room/product_views.py`, `control_room/doc_views.py`).
- **Operations staff-wide access:** Payment confirmation and customer/support views use `StaffRequiredMixin` only (`operations/mixins.py`, `operations/views.py`, `operations/action_views.py`).
- RBAC helpers exist (`accounts/services/rbac.py`) and are used for **team management** (`TeamManagementMixin`) and **platform ops** (`PlatformOwnerMixin`), but not for most destructive admin functions.

### MEDIUM
- Uneven audit coverage: manual payment confirmation and some support actions may not emit security audit events.

### CLEAN
- Customer portal uses `PortalMixin` / queryset scoping.
- Payment proof download enforces owner-or-staff authorization (`payments/views.py`).
- Platform owner and team management mixins correctly enforce RBAC where applied.

---

## 5. Middleware & security headers

### CLEAN
- Custom security header middleware applies CSP, Permissions-Policy, Referrer-Policy (`accounts/middleware.py`, `config/settings/base.py`).
- `X-Frame-Options=DENY`, nosniff, HttpOnly/SameSite cookies configured in base settings.

### HIGH
- **CSP allows `'unsafe-inline'` scripts** (`config/settings/base.py` `SECURITY_CSP`). Weakens XSS protection; tightening requires site-wide verification.

### MEDIUM
- Permissions-Policy present in Django middleware; nginx vhost on production does not duplicate all headers (relies on Django for apex traffic).

---

## 6. Media, static files & private uploads

### CLEAN
- Private payment proofs use `private_payment_proof_upload_to` path (`payments/models/payment.py`, migration `0002`).
- Django URL layer blocks public serving of private/legacy proof paths (`config/urls.py`, `core/media_paths.py`).
- Authenticated proof download view with authorization tests (`payments/tests/test_private_media.py`).
- Repo nginx configs include private-media deny blocks (`deploy/nginx/zreta.com.conf`, `deploy/nginx/zreta.com-marketing.conf`).

### HIGH
- **Live production nginx has no `/media/private/` or `/media/payments/proofs/` deny blocks** and no static/media aliases — all traffic proxied to Gunicorn. Defense relies on Django only at the application layer.
- **S3 optional config disables query-string auth** (`AWS_QUERYSTRING_AUTH = False` in `production.py`). If S3 is enabled with a permissive bucket policy, private objects could be directly accessible.

### MEDIUM
- `proof_document` FileField has no explicit size/type/content validation beyond Django defaults.
- Proof downloads served inline (not forced attachment) — lower browser exposure risk.

### LOW
- Production `media/` directory owned `churchhub:churchhub` while service runs as `marketing` — verify write paths still work for uploads (logs dir already `marketing:marketing-runtime`).

---

## 7. Logging & auditability

### CLEAN
- Rotating file handlers for app and security logs (`config/settings/base.py`).
- Security logger namespace with dedicated file handler.
- Audit event model and helpers exist (`accounts/models/audit.py`, `accounts/services/audit.py`).
- Rate-limit exceed events logged.

### MEDIUM
- Gunicorn/nginx log rotation depends on host logrotate, not fully defined in repo.
- Audit log records are not append-only at DB level.
- Session revoke/logout tracking incomplete (metadata vs Django session deletion).

### LOW
- Health endpoint may include raw exception strings on failure (`core/views.py`).

---

## 8. Database & Redis

### CLEAN
- Production rejects SQLite (`production.py`).
- PostgreSQL credentials from environment (verified on VPS: `DB_NAME=marketing`, `DB_USER=marketing`, `DB_HOST=127.0.0.1`).
- Redis required in production for cache/sessions (`apply_redis_settings(..., require=True)`).
- `pg_isready` reports PostgreSQL accepting connections on VPS.

### MEDIUM
- Base settings define fallback DB password string; production does not explicitly reject known-default DB passwords (only secret key).
- Redis not verified for public exposure in this audit (expected localhost-only).

---

## 9. Backups & disaster recovery

### CLEAN
- Backup scripts: `pg_dump` custom format, media tar, manifests, checksum verification, production-restore guard (`deploy/scripts/backup-*.sh`, `restore-database.sh`).
- `backup-all.sh` initializes backup layout before logging (commit `2b3160c`).
- systemd timer units present in repo (`deploy/systemd/zreta-backup.*`).
- VPS now has `/var/backups/zreta` and `/var/log/zreta-backup`.
- Existing docs: `docs/ZRETA_BACKUP_POLICY.md`, `docs/ZRETA_BACKUP_IMPLEMENTATION.md`, `docs/ZRETA_RESTORE_PROCEDURE.md`.

### HIGH
- **Restore drill not verified** on production (`ZRETA_BACKUP_IMPLEMENTATION.md` marks pending).
- **No off-site backup replication** documented or implemented — same-VPS backups do not protect against total VPS loss.
- **No backup failure alerting** (timer/service has no `OnFailure` notification path).

### MEDIUM
- Backup service runs as root without systemd sandboxing (`zreta-backup.service`).
- Retention keeps seven newest backups; weekly/monthly env vars documented but not implemented (`prune-backups.sh` vs policy doc).
- `deploy/env/*.example` templates referenced in docs/scripts but directory is gitignored / not present in checkout — operators must maintain `.env` out of band.

---

## 10. Deployment & systemd configuration

### CLEAN (live production)
- Gunicorn bound to `127.0.0.1:8001` (not publicly exposed).
- Service enabled, active, auto-restart configured.
- Uses `.venv` and `marketing` user as intended by operator.
- Application code at latest `origin/main` SHA.

### HIGH
- **Repo systemd unit does not match production.** Repository file still targets Unix socket via `gunicorn.conf.py` and `Group=www-data`. Production unit uses inline `--bind 127.0.0.1:8001` and `Group=marketing-runtime`.
- **`deploy-app.sh` guard** detects legacy `churchhub`/`:8001` layouts but not all drift scenarios (e.g., reconciled production may still diverge from repo socket config).
- **`setup-nginx.sh`** removes default nginx site — unsafe on shared VPS if used accidentally.

### MEDIUM
- Legacy `/var/www/marketing-site/venv` still on disk (`churchhub` owned) — document before removal.
- Documentation split: `ZRETA_PRODUCTION_TRUTH.md` / `ZRETA_ARCHITECTURE_RECONCILIATION.md` describe reconciliation; live state has partially advanced but nginx/repo systemd not aligned.

### LOW
- Shared VPS hosts other nginx sites (`churchhub`, `business.zreta.com`, `micro.zreta.com`) — out of scope unless changes affect them.

---

## 11. Health checks & monitoring

### CLEAN
- `/health/` is GET-only, uncached, checks DB + cache, returns 503 on DB failure (`core/views.py`).
- Tests exist (`common/tests/test_health.py`).
- Optional Sentry integration with `send_default_pii=False`.

### MEDIUM
- Error responses may leak internal exception text in JSON checks.
- No repo-defined alerting for disk, cert expiry, 5xx rate, or backup failures.

---

## 12. Error handling

### CLEAN
- Custom branded `404` and `500` handlers (`common/views.py`, `templates/errors/`).
- Production `DEBUG=False` prevents Django debug pages.

### MEDIUM
- No custom `400` or `403` handlers registered (`config/urls.py`).

---

## 13. Input validation & web security

### CLEAN
- Django ORM used throughout — no raw SQL injection patterns found in reviewed paths.
- CSRF on state-changing forms (reviewed templates include tokens).
- Webhook CSRF exempt with signature verification (`payments/views.py`).
- Checkout pricing validated server-side (tests in `payments/tests/test_checkout_security.py`).

### MEDIUM
- Open redirect risk should be reviewed on any user-supplied `next` parameters (not exhaustively audited here).
- File upload validation for proofs could be stronger.

---

## 14. Rate limiting

### CLEAN
- Redis/cache-backed rate limiting for login, MFA verify, password reset scopes (`accounts/services/rate_limit.py`).
- Configurable limits in settings (`AUTH_LOGIN_RATE_LIMIT`, etc.).

### MEDIUM
- Contact/demo forms and registration not clearly rate-limited at application layer.
- IP derivation trust boundary depends on nginx configuration.

---

## 15. Dependencies

### CLEAN
- Production requirements exclude dev tools (`requirements/production.txt`).
- Core stack pinned with compatible ranges (`requirements/base.txt`).

### MEDIUM
- No fully locked production lockfile — reproducibility depends on pip resolution time.
- Dependency CVE scanning not automated in repo.

---

## 16. Secrets & file permissions

### CLEAN
- `.env` gitignored; backup artifacts gitignored.
- Production `.env` on VPS: mode **640**, group `marketing-runtime` (matches operator intent).
- No hard-coded production secrets found in source (pattern matches are env var names, tests, and form fields).

### MEDIUM
- `.gitignore` could be expanded for `*.pem`, `*.key`, dumps, `.env.production`, etc.
- `media/` permissions `775` and mixed ownership (`churchhub` vs `marketing`) — review against least privilege.
- Legacy `venv/` and any local secret copies not inventoried on VPS in this pass.

---

## 17. Testing & CI baseline (local, 2026-08-13)

| Check | Result |
|-------|--------|
| `python manage.py check` (test settings) | **Pass** — 0 issues |
| `python manage.py test` (112 tests, test settings) | **Pass** |
| Security-focused tests present | deploy guard, private media, checkout, webhooks, MFA, auth flows, backup manifest |

### MEDIUM
- `check --deploy` under production settings not run in this Windows dev environment (requires production `.env`).
- No dedicated tests for invitation existing-user login path or MFA rescan bypass risk.
- CI does not execute production-settings deploy check.

---

## 18. SOC 2 foundation (informational only)

Not implementing SOC 2. Existing controls that would help a future readiness program:

- Production configuration guards and HTTPS enforcement
- RBAC scaffolding (partially applied)
- Audit event logging (partial coverage)
- Backup/restore tooling and documentation
- Webhook signature validation and payment hardening tests
- Private media access controls
- Rate limiting infrastructure

Gaps a future SOC 2 program would likely require: formal access reviews, comprehensive audit coverage, backup restore testing evidence, off-site backups, vulnerability management, incident response drills, and consistent least-privilege RBAC enforcement.

---

## Recommended remediation order (Phase 2+ — not executed here)

| Priority | Item | Phase |
|----------|------|-------|
| 1 | Fix invitation existing-user authentication gap | App security |
| 2 | Re-evaluate MFA verify rescan policy (require step-up auth or remove from verify flow) | App security |
| 3 | Align repo systemd/gunicorn/nginx with live `:8001` / `marketing-runtime` architecture OR complete socket migration deliberately | Infra |
| 4 | Add nginx static/media aliases + private-media deny blocks on production | Infra |
| 5 | Apply RBAC mixins to high-risk control-room/operations views | Authorization |
| 6 | Execute and document backup restore drill + off-site copy | DR |
| 7 | Tighten CSP progressively with site verification | Headers |
| 8 | Remove/document legacy `venv/` after dependency verification | Cleanup |
| 9 | Expand tests for production settings guard and auth edge cases | Testing |

---

## Phase 1 exit criteria

| Criterion | Status |
|-----------|--------|
| Repository inspected across listed domains | **Complete** |
| Read-only production discovery performed | **Complete** (partial sudo/nginx limits noted) |
| Findings classified CRITICAL → CLEAN | **Complete** |
| Application code modified | **No** (by design) |
| Ready for Phase 2 implementation planning | **Yes** |

---

## Related documents

| Document | Purpose |
|----------|---------|
| `docs/ZRETA_PRODUCTION_TRUTH.md` | Production vs repository state |
| `docs/ZRETA_ARCHITECTURE_RECONCILIATION.md` | Infrastructure reconciliation concept |
| `docs/ZRETA_BACKUP_POLICY.md` | Backup policy |
| `docs/ZRETA_BACKUP_IMPLEMENTATION.md` | Backup implementation status |
| `docs/ZRETA_RESTORE_PROCEDURE.md` | Restore procedure |
