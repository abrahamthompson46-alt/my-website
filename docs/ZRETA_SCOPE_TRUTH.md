# Zreta Platform — Scope Truth Matrix

**Last updated:** 2026-09-14 (storefront + external CoreTrust model)  
**Purpose:** Authoritative statement of what the repository implements today vs. what is planned.

**Product model:** See `docs/ZRETA_PRODUCT_MODEL.md`. This repo is the **marketing + billing platform**. Live vertical products (ChurchHub, CoreTrust) run as **separate applications**.

Legend:
- **IMPLEMENTED** — Exists in production code and is testable
- **PARTIALLY IMPLEMENTED** — Some capability exists with known gaps
- **PLANNED** — Roadmap item; not in application code
- **EXTERNAL** — Delivered by a separate product app, not this repo
- **NOT IMPLEMENTED** — Does not exist; marketing may reference as future product

---

## Platform foundation

| Capability | Status | Evidence |
|------------|--------|----------|
| Django 5 monolith | IMPLEMENTED | `config/settings/` |
| PostgreSQL (production) | IMPLEMENTED | `production.py` |
| Redis cache/sessions (production) | IMPLEMENTED | `config/redis_settings.py` |
| Server-rendered public website | IMPLEMENTED | `website/`, `templates/` |
| CMS-driven homepage | IMPLEMENTED | `cms/`, `website/services/homepage.py` |
| Customer portal | IMPLEMENTED | `customer_portal/` |
| Staff operations dashboard | IMPLEMENTED | `operations/` |
| Platform control room | IMPLEMENTED | `control_room/` |
| REST API (`/api/v1/*`) | IMPLEMENTED | `api/` + `docs/API_V1.md` |
| Background job queue (Celery) | IMPLEMENTED | Celery + Redis; `docs/CELERY.md` |
| Structured logging | IMPLEMENTED | JSON formatter + request_id; `docs/OBSERVABILITY.md` |
| Prometheus metrics | IMPLEMENTED | Token-gated `/metrics/` |
| Multi-tenant organizations | IMPLEMENTED | `organizations/` app |
| In-repo MFI ledger / borrower engine | NOT IMPLEMENTED | Removed; CoreTrust is external |
| SAML/OAuth SSO | NOT IMPLEMENTED | Seed/demo copy only |

---

## Identity, auth, and access

| Capability | Status | Evidence |
|------------|--------|----------|
| Email/password login | IMPLEMENTED | `accounts/` |
| Email verification (customers) | IMPLEMENTED | `EmailVerifiedRequiredMixin` |
| TOTP MFA (staff) | IMPLEMENTED | `accounts/services/mfa.py` |
| Staff MFA enforcement | IMPLEMENTED | `StaffMFARequiredMiddleware` |
| RBAC (platform owner/admin) | IMPLEMENTED | `accounts/services/rbac.py` |
| Account lockout + auth rate limits | IMPLEMENTED | `accounts/backends.py`, `rate_limit.py` |
| Session tracking/revocation | PARTIALLY IMPLEMENTED | Redis session revocation gap documented |
| Organization-scoped RBAC | PLANNED | Requires tenant model |

---

## Billing and payments

| Capability | Status | Evidence |
|------------|--------|----------|
| Product catalog + pricing plans | IMPLEMENTED | `products/` |
| Subscription + invoice records | IMPLEMENTED | `customer_portal/models/` |
| Checkout (plan/invoice) | IMPLEMENTED | `payments/views.py` |
| Server-side authoritative pricing | IMPLEMENTED (Phase 0) | `payments/services/pricing.py` |
| Paystack / Flutterwave / Hubtel | IMPLEMENTED | `payments/gateways/` |
| Manual/offline payments | IMPLEMENTED | `ManualGateway` |
| Webhook verification | IMPLEMENTED | `payments/services/webhooks.py` |
| Refunds (service layer) | PARTIALLY IMPLEMENTED | Limited test coverage |
| Private payment proof downloads | IMPLEMENTED (Phase 0) | `PaymentProofDownloadView` |

---

## Core banking / CoreTrust

| Capability | Status | Notes |
|------------|--------|-------|
| CoreTrust live MFI product | EXTERNAL | Deployed separately (e.g. `micro.zreta.com`); not this repo |
| Catalog + portal billing for CoreTrust | IMPLEMENTED | Product slug `microfinance-core`, external app URLs |
| Loan / savings / GL inside this repo | NOT IMPLEMENTED | By design — belongs in CoreTrust |

**Do not claim that this repository is a core-banking system.** Banking capability is CoreTrust’s.

---

## Modular products (marketing catalog)

| Product | Site status (seed) | Live backend |
|---------|-------------------|--------------|
| ChurchHub | Generally Available | EXTERNAL (`mychurch.zreta.com`); portal billing here |
| CoreTrust | Generally Available | EXTERNAL (`micro.zreta.com`); portal billing here |
| ERP Suite | Catalog entry | NOT IMPLEMENTED in this repo |
| School Management | Catalog entry | NOT IMPLEMENTED in this repo |
| Hospital Management | Catalog entry | NOT IMPLEMENTED in this repo |
| HR & Payroll | Catalog entry | NOT IMPLEMENTED in this repo |
| Retail Commerce | Coming Soon | NOT IMPLEMENTED |

---

## Documentation content

| Content type | Status | Notes |
|--------------|--------|-------|
| Public docs articles/videos | IMPLEMENTED | `documentation/` |
| Fake live API endpoint catalog | REMOVED (Phase 0 seed) | Was misleading; replaced with Roadmap articles |
| Architecture/multi-tenant claims in seed | CORRECTED (Phase 0) | Fresh seeds use honest copy |

**Existing databases** seeded before this realignment may still contain old “Microfinance Core / planned” copy until migrated or re-seeded.

---

## Infrastructure

| Capability | Status |
|------------|--------|
| Nginx + Gunicorn + systemd deploy templates | IMPLEMENTED |
| Docker Compose (dev) | IMPLEMENTED |
| GitHub Actions CI (tests + checks) | IMPLEMENTED |
| CI/CD auto-deploy to production | NOT IMPLEMENTED |
| Automated DB backups in repo | PARTIALLY IMPLEMENTED | Scripts exist; restore drill pending |

---

## How to use this document

- **Sales/marketing:** Claim IMPLEMENTED platform features and EXTERNAL live products (ChurchHub, CoreTrust) accurately.
- **Engineering:** Build storefront/portal/billing here; build domain engines in each product’s own codebase.
- **Security/compliance:** This repo is not CoreTrust and is not a core banking system.

See also: `docs/ZRETA_PRODUCT_MODEL.md`, `docs/ZRETA_UPGRADE_ROADMAP.md`.
