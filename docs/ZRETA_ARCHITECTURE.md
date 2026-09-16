# Zreta Platform — Architecture Overview

**Audit date:** 2026-08-13  
**Repository:** `my-website` (Django monolith)  
**Scope:** As-is architecture before enterprise upgrade

---

## Executive classification

This repository is a **Django marketing/CMS and customer subscription platform**, not a full core-banking or multi-tenant fintech system. It provides:

- Public marketing website (products, blog, docs, careers, contact)
- Customer portal (subscriptions, invoices, licenses, tickets, downloads)
- Payment collection (Paystack, Flutterwave, Hubtel, manual)
- Staff operations (`/ops/`) and platform control room (`/control/`)
- CMS-driven homepage and content management

**Advertised but not implemented in code:** Microfinance Core (loans, savings, ledger), REST API (`/api/v1/*`), organization-level multi-tenancy, SAML SSO (seed content only).

---

## High-level diagram

```
                    ┌─────────────────────────────────────────┐
                    │           Nginx (TLS terminate)          │
                    └────────────────────┬────────────────────┘
                                         │
                    ┌────────────────────▼────────────────────┐
                    │     Gunicorn → Django (config.wsgi)      │
                    │  Middleware: Security, CSRF, Auth, MFA   │
                    └─────┬──────────────┬──────────────┬─────┘
                          │              │              │
              ┌───────────▼──┐  ┌────────▼────┐  ┌─────▼─────┐
              │ PostgreSQL   │  │ Redis       │  │ Media     │
              │ (prod)       │  │ cache/sess  │  │ local/S3  │
              └──────────────┘  └─────────────┘  └───────────┘
                          │
              ┌───────────▼──────────────────────────┐
              │ External: Paystack/Flutterwave/Hubtel │
              │ SMTP, optional S3, optional Sentry    │
              └──────────────────────────────────────┘
```

---

## Project structure

| Path | Purpose |
|------|---------|
| `config/` | Settings (base/dev/staging/production/test), URLs, WSGI, Redis helper, env loader |
| `accounts/` | Custom User (UUID PK), auth, MFA, RBAC, sessions, audit, invitations |
| `website/` | Homepage, legal pages, status |
| `cms/` | CMS pages, sections, hero, testimonials, news |
| `marketing/` | Blog, events, newsletters, case studies, whitepapers |
| `products/` | Product catalog, pricing, comparisons, demo requests |
| `documentation/` | Public docs articles/videos/downloads (content, not API) |
| `customer_portal/` | Logged-in customer area |
| `payments/` | Checkout, webhooks, refunds, reconciliation records |
| `operations/` | Staff ops dashboard, demo request management |
| `control_room/` | Platform owner/admin configuration UI |
| `partners/` | Partner dashboard (lightweight) |
| `contact/`, `support/`, `careers/` | Public forms and pages |
| `core/` | Base models, health check, SEO, middleware, sitemaps |
| `common/` | Shared utilities, navigation, template tags, email branding |
| `templates/` | Server-rendered Django templates |
| `static/` | CSS, JS, images, design tokens |
| `frontend/shared-ui/tokens/` | Design token JSON/CSS |
| `deploy/` | Nginx, Gunicorn, systemd, env examples, provisioning scripts |
| `docs/` | Deployment and design documentation |

---

## Django applications (18 local + Django/contrib)

### Public / marketing
- **website** — Homepage assembly via CMS + services (`website/services/homepage.py`)
- **cms** — Structured page content, hero banners, section items
- **marketing** — Blog and content marketing
- **products** — Product pages, pricing, comparison, demo forms
- **documentation** — Help center content
- **pages**, **blog** — Static/legacy routing
- **contact**, **support**, **careers**, **partners** — Lead capture and support entry points

### Authenticated customer
- **customer_portal** — Dashboard, subscriptions, invoices, licenses, tickets, profile
- **payments** — Customer checkout at `/app/payments/`

### Staff / platform
- **operations** — Revenue/demo analytics for staff
- **control_room** — Products, branding, nav, team, platform ops (email, GitHub deploy)
- **accounts** — Identity layer shared by all portals

### Infrastructure
- **core**, **common** — Cross-cutting concerns

---

## Request routing (`config/urls.py`)

| Prefix | App | Auth |
|--------|-----|------|
| `/` | website | Public |
| `/products/` | products | Public |
| `/docs/` | documentation | Public |
| `/accounts/` | accounts | Mixed |
| `/app/` | customer_portal | Login + email verified |
| `/app/payments/` | payments | Login + email verified |
| `/ops/` | operations | Staff + MFA |
| `/control/` | control_room | Staff + MFA + RBAC |
| `/admin/` | Django admin | Staff + MFA |
| `/payments/webhooks/<gateway>/` | payments | CSRF-exempt, signature verified |
| `/health/` | core | Public |

---

## Frontend architecture

**Pattern:** Server-rendered Django templates + progressive enhancement (vanilla JS).

| Layer | Technology |
|-------|------------|
| Templates | Django template language, partials, `ui_tags` component tags |
| CSS | Custom design system (`static/css/`), page-scoped CSS |
| JS | Minimal (`home.js`, `screenshot-lightbox.js`) — no React/Vue SPA |
| Design tokens | `frontend/shared-ui/tokens/tokens.css` included in static |
| Static serving | WhiteNoise (compressed), Nginx alias in production |
| SEO | `core/seo/` metadata, JSON-LD schema, sitemaps |

**No separate frontend build pipeline** (no Webpack/Vite). No REST API consumed by SPA.

---

## Service layer pattern

Business logic is extracted selectively into `services/` modules:

| Module | Responsibility |
|--------|----------------|
| `accounts/services/` | MFA, RBAC, sessions, rate limits, audit, invitations |
| `payments/services/` | Checkout, webhooks, refunds, billing sync |
| `customer_portal/services.py` | Dashboard stats, notifications |
| `cms/services.py` | Homepage context merge |
| `website/services/homepage.py` | Featured products, trust signals |
| `control_room/services/` | Deploy, email delivery, cache health |
| `common/services/` | Demo requests, trial provisioning, email branding |

Views remain thin in newer code; some legacy views still contain form handling inline.

---

## Data model conventions

- **BaseModel** (`core/models/__init__.py`): UUID primary keys + created/updated timestamps
- **User scoping**: Customer resources use `ForeignKey("accounts.User")` + queryset filters
- **No tenant/org FK** on business models
- **Money**: `Decimal` fields + `common/money.py` helpers (quantize, minor units)

---

## Authentication flow

1. Email/password via `EnterpriseAuthBackend` (lockout after 5 failures)
2. Optional TOTP MFA challenge post-login
3. Staff must enroll MFA before accessing `/admin/`, `/control/`, `/ops/` (`StaffMFARequiredMiddleware`)
4. Customer portal requires verified email (`EmailVerifiedRequiredMixin`)
5. Sessions tracked in `UserSession` model; revocation supported

---

## RBAC model

- **Role** → Django **Permission** (many-to-many)
- **UserRole** assigns roles; permissions synced to `user.user_permissions`
- Built-in role slugs: `platform-owner`, `platform-admin`
- Custom permission: `control_room.manage_platform_operations`
- Enforcement via mixins: `PermissionRequiredMixin`, `PlatformOwnerMixin`, `TeamManagementMixin`

---

## Payment architecture

Gateway adapter pattern in `payments/gateways/`:

- Registry resolves adapter by `GatewayConfiguration.code`
- Checkout creates `Payment` record, initiates gateway authorization
- Webhooks CSRF-exempt; signature verification per adapter
- Webhook idempotency via `WebhookEvent.event_id` unique per gateway
- Billing sync updates invoices/subscriptions on success/failure

---

## Background processing

**None configured.** No Celery, RQ, Django-Q, or cron schedules. Email sending and webhook processing are synchronous in request handlers.

---

## Caching

- Development/fallback: `LocMemCache`
- Production/staging: Redis via `REDIS_URL` (`config/redis_settings.py`)
- Redis also backs sessions in production
- Public pages cached with `@cache_page` (homepage, etc.)
- Rate limits use cache keys `ratelimit:*`

---

## External integrations

| Integration | Location | Purpose |
|-------------|----------|---------|
| Paystack | `payments/gateways/paystack.py` | Card/MoMo payments |
| Flutterwave | `payments/gateways/flutterwave.py` | Payments |
| Hubtel | `payments/gateways/hubtel.py` | Ghana MoMo |
| SMTP | Django email settings | Transactional email |
| AWS S3 | Optional `django-storages` | Media in production |
| Sentry | Optional in production settings | Error monitoring |
| GitHub | `control_room/services/deploy.py` | Platform owner git pull deploy |

---

## Deployment topology

- **Docker Compose**: web + PostgreSQL 16 + Redis 7 (local/dev)
- **VPS**: Nginx → Unix socket Gunicorn → Django
- **systemd**: `deploy/systemd/marketing-site.service` (hardened unit)
- **CI**: GitHub Actions — `check --deploy`, migration drift, full test suite

---

## Key architectural gaps (for upgrade planning)

1. No API layer (DRF) — all server-rendered
2. No multi-tenant data model — single-platform, per-user isolation
3. No core banking domain — payments are subscription/checkout only
4. No async job queue — scalability and reliability limits
5. Documentation/marketing references features not implemented in code

See companion audits for security, database, financial, multi-tenancy, tests, deployment, and roadmap.
