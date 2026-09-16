# Zreta Platform — Technical Audit

**Audit date:** 2026-08-13  
**Auditor role:** Senior Software Architect / Security Engineer  
**Method:** Read-only repository analysis + test execution  
**Commit baseline:** `cbbbac9` (main)

---

## 1. Overall project structure

| Finding | Severity | Location | Evidence |
|---------|----------|----------|----------|
| Monolithic Django 5.x application with clear app boundaries | INFORMATIONAL | `config/settings/base.py` | 18 local apps in `LOCAL_APPS` |
| No microservices or separate API service | INFORMATIONAL | Entire repo | Single WSGI app |
| Marketing platform mislabeled as full enterprise fintech in seed content | MEDIUM | `products/seed_products.py`, `documentation/seed_documentation.py` | Loans/ledger/API docs are marketing copy only |
| Design tokens exist but no component build pipeline | LOW | `frontend/shared-ui/tokens/` | Static CSS tokens only |

---

## 2. Django applications and responsibilities

Documented in `ZRETA_ARCHITECTURE.md`. All apps have defined `apps.py` and URL modules. Control room and operations are well-separated from customer portal.

**Strength:** Clear separation between public, customer, and staff surfaces.  
**Gap:** `partners` app appears lightly used; scope unclear without production traffic data.

---

## 3. Frontend architecture

| Finding | Severity | Location | Why it matters |
|---------|----------|----------|----------------|
| Server-rendered templates only | INFORMATIONAL | `templates/` | Simple to secure; limits SPA scalability |
| CSP allows `'unsafe-inline'` scripts/styles | MEDIUM | `config/settings/base.py:356-363` | Reduces XSS mitigation effectiveness |
| Minimal JS — low client-side attack surface | INFORMATIONAL | `static/js/` | 2 JS files for homepage/lightbox |
| No frontend dependency lockfile (npm) | INFORMATIONAL | Repo root | No Node supply-chain surface |

---

## 4. Database models and relationships

| Finding | Severity | Location | Evidence |
|---------|----------|----------|----------|
| UUID PKs on BaseModel entities | INFORMATIONAL | `core/models/__init__.py` | Non-sequential IDs reduce enumeration |
| User-centric FK scoping for portal data | INFORMATIONAL | `customer_portal/models/`, `payments/models/payment.py` | `user = ForeignKey(User)` |
| No Organization/Tenant model | HIGH (for fintech roadmap) | Grep across models | Zero tenant fields |
| AuditLog not append-only at DB level | MEDIUM | `accounts/models/audit.py` | No DB trigger preventing UPDATE/DELETE |
| Payment.reference and idempotency_key unique | INFORMATIONAL | `payments/models/payment.py:45-47` | Supports deduplication |

---

## 5. PostgreSQL / database configuration

| Finding | Severity | Location | Evidence |
|---------|----------|----------|----------|
| PostgreSQL required in production | INFORMATIONAL | `config/settings/production.py:29-30` | Raises if SQLite |
| Connection pooling via CONN_MAX_AGE=600 | INFORMATIONAL | `config/settings/base.py:135` | Standard Django persistent connections |
| Tests use SQLite in-memory | INFORMATIONAL | `config/settings/test.py` | Fast but not prod-parity |
| No read replicas or routing | INFORMATIONAL | Settings | Single `default` DB |
| connect_timeout=10 | INFORMATIONAL | `base.py:137` | Basic resilience |

---

## 6. Authentication and user management

| Finding | Severity | Location | Evidence |
|---------|----------|----------|----------|
| Custom User with email login | INFORMATIONAL | `accounts/models/user.py` | `AUTH_USER_MODEL = accounts.User` |
| Account lockout after 5 failures / 30 min | INFORMATIONAL | `accounts/backends.py`, `base.py:379-380` | Implemented |
| Auth rate limits (login, password reset, MFA) | INFORMATIONAL | `accounts/services/rate_limit.py` | Cache-backed |
| TOTP MFA + backup codes for staff | INFORMATIONAL | `accounts/services/mfa.py` | pyotp + hashed backup codes |
| Staff MFA enforced globally | INFORMATIONAL | `accounts/middleware.py:51-74` | Redirects to enroll |
| Session revocation may not invalidate Redis cache sessions | MEDIUM | `accounts/services/sessions.py:59-74` | Deletes `django.contrib.sessions.models.Session` only |
| Invitation links: 1-hour TTL, one-time token burn | INFORMATIONAL | `accounts/models/invitation.py`, tests | Verified in `test_team_management.py` |

---

## 7. RBAC and permissions

| Finding | Severity | Location | Evidence |
|---------|----------|----------|----------|
| Role → Permission sync to user_permissions | INFORMATIONAL | `accounts/services/rbac.py:54-60` | Works; tested |
| Superuser bypasses all checks | INFORMATIONAL | `rbac.py:13-14, 43-44` | Standard Django pattern |
| Platform ops restricted to owner or explicit permission | INFORMATIONAL | `control_room/mixins.py:32-39` | Tested |
| Permission denied events audit-logged | INFORMATIONAL | `accounts/mixins.py:18-29` | Good |
| No field-level or object-level permissions (django-guardian) | MEDIUM | — | Relies on queryset scoping in views |

---

## 8. Multi-tenancy and tenant isolation

**Status: NOT IMPLEMENTED**

See `ZRETA_MULTITENANCY_AUDIT.md`. Isolation is **per-user**, not per-organization.

---

## 9. API architecture and endpoints

| Finding | Severity | Location | Evidence |
|---------|----------|----------|----------|
| No Django REST Framework | INFORMATIONAL | `requirements/` | Not in dependencies |
| No `/api/v1/` routes | INFORMATIONAL | `config/urls.py` | Only `/health/` JSON + webhooks |
| Documentation app stores fake API paths | MEDIUM | `documentation/seed_documentation.py` | `/api/v1/users` is content only |

Machine endpoints:
- `GET /health/` — DB + cache probe
- `POST /payments/webhooks/<gateway_code>/` — payment provider callbacks

---

## 10. Business logic and service layers

Partial service-layer adoption. Newer modules (payments, accounts, homepage) use services; some views still inline logic.

| Finding | Severity | Location |
|---------|----------|----------|
| Checkout amount can be supplied via raw POST when no invoice/plan | HIGH | `payments/views.py:145-154` |
| GitHub deploy runs subprocess git pull as web user | HIGH | `control_room/services/deploy.py` |
| Demo request rate limiting shared with auth cache | INFORMATIONAL | `common/services/demo_requests.py` |

---

## 11–13. Financial / loans / savings

**Not implemented.** See `ZRETA_FINANCIAL_AUDIT.md`. Only subscription payment collection exists.

---

## 14. Background jobs / tasks

| Finding | Severity | Location | Evidence |
|---------|----------|----------|----------|
| No Celery/RQ/cron | MEDIUM | Repo-wide grep | Email/webhooks synchronous |
| Webhook processing in HTTP request thread | MEDIUM | `payments/views.py:234-254` | Timeout risk under load |

---

## 15. Caching and Redis

| Finding | Severity | Location | Evidence |
|---------|----------|----------|----------|
| Redis required in production | INFORMATIONAL | `production.py:45-51` | Startup fails without REDIS_URL |
| LocMem fallback in dev | INFORMATIONAL | `base.py:424-428` | Rate limits not shared across workers |
| Cache health diagnostics in control room | INFORMATIONAL | `control_room/services/cache_health.py` | Operational visibility |

---

## 16. File / document handling

| Finding | Severity | Location | Evidence |
|---------|----------|----------|----------|
| Local media served publicly via Nginx + Django | HIGH | `deploy/nginx/marketing-site.conf:72-77`, `config/urls.py:31-46` | `/media/` unauthenticated |
| Payment proof uploads at `payments/proofs/` | HIGH | `payments/models/payment.py:148` | Potentially sensitive |
| Brand upload validators (extension, size) | INFORMATIONAL | `control_room/validators.py` | SVG/logo validated |
| Optional S3 with public custom domain | MEDIUM | `production.py:65-86` | ACL=None; no signed URLs |

---

## 17. External integrations

Documented in architecture doc. Gateway secrets via environment only (`base.py:388-418`) — good practice.

---

## 18. Security configuration

See `ZRETA_SECURITY_AUDIT.md` for full findings.

Production hardening highlights:
- SECRET_KEY length validation
- ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS enforcement
- HSTS, secure cookies, SSL redirect
- Custom CSP + security headers middleware

---

## 19. Environment variables and secrets

| Finding | Severity | Location | Evidence |
|---------|----------|----------|----------|
| `.env` gitignored | INFORMATIONAL | `.gitignore` | No secrets in repo |
| Example env files with placeholders | INFORMATIONAL | `.env.example`, `.env.production.example` | Safe |
| Default insecure SECRET_KEY in base (dev only) | MEDIUM | `base.py:11-14` | Blocked in production |
| Payment gateway keys from env, not DB | INFORMATIONAL | `base.py:390-414` | Correct pattern |
| Docker compose default postgres password `changeme` | LOW | `docker-compose.yml` | Dev only |

---

## 20. Django production configuration

| Control | Status | Location |
|---------|--------|----------|
| DEBUG=False enforced | ✅ | `production.py:7` |
| Whitenoise static | ✅ | Middleware + STORAGES |
| Sentry optional | ✅ | `production.py:88-99` |
| django-extensions removed in prod | ✅ | `production.py:54` |
| Admin email on errors | ✅ | LOGGING mail_admins |

---

## 21–22. Nginx / Gunicorn / deployment / CI

See `ZRETA_DEPLOYMENT_AUDIT.md`.

---

## 23. Automated tests

See `ZRETA_TEST_AUDIT.md`. **72 tests, all passing.** No coverage tooling configured.

---

## 24. Error handling

| Finding | Severity | Location |
|---------|----------|----------|
| Custom 404/500 handlers | INFORMATIONAL | `common/views.py` |
| Webhook errors logged, generic JSON returned | INFORMATIONAL | `payments/views.py:248-250` |
| Health endpoint exposes DB error strings | LOW | `core/views.py:25-27` |
| Payment receipt email failure swallowed | LOW | `payments/views.py:225-226` |

---

## 25. Logging and monitoring

| Component | Location |
|-----------|----------|
| Rotating file logs | `logs/django.log`, `error.log`, `security.log` |
| Request ID middleware | `core/middleware.py` |
| Security logger | `security` logger in LOGGING |
| Sentry optional | Production settings |
| No APM/metrics beyond health | — |

---

## 26. Database indexes and constraints

| Model | Indexes | Gap |
|-------|---------|-----|
| Payment | `status+created_at`, `gateway_reference` | No index on `user+created_at` for portal lists |
| AuditLog | `event_type+created_at`, `user+created_at` | Adequate for current scale |
| WebhookEvent | Unique `(gateway, event_id)` | Good for idempotency |

No explicit DB-level constraints preventing audit log mutation.

---

## 27. Performance risks

| Risk | Severity | Detail |
|------|----------|--------|
| N+1 queries in some list views | MEDIUM | Partial `select_related` usage |
| Synchronous webhook processing | MEDIUM | Blocks Gunicorn worker |
| Homepage `@cache_page(300)` | LOW | Good for public traffic |
| No query count monitoring | LOW | — |
| Public media via Django in DEBUG-off mode | MEDIUM | Extra Python overhead for uploads |

---

## 28. Code duplication

| Area | Severity | Detail |
|------|----------|--------|
| Demo form handling duplicated | LOW | `website/views.py`, `products/views.py`, `contact/views.py` |
| Section header fallbacks in templates | LOW | CMS partial + inline defaults |
| Partner logos template orphaned | LOW | `partner_logos.html` unused after homepage upgrade |

---

## 29. Dead or unused code

| Item | Location |
|------|----------|
| `templates/website/partials/partner_logos.html` | No longer included in home.html |
| `LEGACY_HOME_SECTIONS partner_logos` | `cms/constants.py` — intentional deprecation |
| SMS/WebAuthn MFA enum values | `accounts/models/security.py` — no implementation |

---

## 30. Technical debt

| Item | Priority |
|------|----------|
| No multi-tenancy despite marketing claims | Critical for fintech roadmap |
| No core banking domain | Critical for Microfinance product |
| No REST API | High for integrations |
| No background job system | High |
| CSP unsafe-inline | Medium |
| Public media for sensitive uploads | High |
| Session revocation + Redis mismatch | Medium |
| Test coverage gaps (payments portal, IDOR) | Medium |

---

## 31. Documentation

| Doc | Status |
|-----|--------|
| `docs/DEPLOYMENT.md`, `DEPLOYMENT-ZRETA.md` | Present, operational |
| `docs/PRODUCTION-READINESS.md` | Present, checklist-style |
| `docs/design-system/` | Present |
| Inline API docs in seed | Misleading (not real API) |
| Architecture/security audits | **This audit series (new)** |

---

## 32. SEO / public website architecture

| Component | Location |
|-----------|----------|
| Homepage CMS merge | `cms/services.build_home_context`, `website/services/homepage.py` |
| SEO metadata | `core/seo/context.py`, template tags |
| JSON-LD schema | `core/seo/schema.py` |
| Sitemaps | `core/sitemaps.py` |
| robots.txt | Cached 24h |
| Recent honest marketing upgrade | `cbbbac9` — ChurchHub-first, no inflated stats |

---

## Audit methodology notes

- No production code modified
- Full test suite executed: 72/72 pass
- No coverage.py installed — coverage percentage not measured
- Production runtime not accessed — deployment findings from config templates only
