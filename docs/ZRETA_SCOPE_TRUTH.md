# Zreta Platform — Scope Truth Matrix

**Last updated:** 2026-08-13 (Phase 0)  
**Purpose:** Authoritative statement of what the repository implements today vs. what is planned.

Legend:
- **IMPLEMENTED** — Exists in production code and is testable
- **PARTIALLY IMPLEMENTED** — Some capability exists with known gaps
- **PLANNED** — Roadmap item; not in application code
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
| REST API (`/api/v1/*`) | NOT IMPLEMENTED | No DRF; no API routes |
| Background job queue (Celery/RQ) | NOT IMPLEMENTED | No task workers |
| Multi-tenant organizations | NOT IMPLEMENTED | No Organization model |
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

## Core banking / Microfinance Core

| Capability | Status | Notes |
|------------|--------|-------|
| Loan origination | NOT IMPLEMENTED | Product marketing only |
| Loan disbursement | NOT IMPLEMENTED | — |
| Repayment allocation | NOT IMPLEMENTED | — |
| Savings accounts | NOT IMPLEMENTED | — |
| Interest accrual | NOT IMPLEMENTED | — |
| General ledger / double-entry | NOT IMPLEMENTED | — |
| Journal entries | NOT IMPLEMENTED | — |
| Business date / period close | NOT IMPLEMENTED | — |
| Regulatory reporting | NOT IMPLEMENTED | — |

**Microfinance Core** on the public site is **product positioning / roadmap**, not a live module in this repository.

---

## Modular products (marketing catalog)

| Product | Site status (seed) | Live backend in repo |
|---------|-------------------|----------------------|
| ChurchHub | Generally Available | External app URLs; portal billing |
| Microfinance Core | Catalog entry | NOT IMPLEMENTED |
| ERP Suite | Catalog entry | NOT IMPLEMENTED |
| School Management | Catalog entry | NOT IMPLEMENTED |
| Hospital Management | Catalog entry | NOT IMPLEMENTED |
| HR & Payroll | Catalog entry | NOT IMPLEMENTED |
| Retail Commerce | Coming Soon | NOT IMPLEMENTED |

---

## Documentation content

| Content type | Status | Notes |
|--------------|--------|-------|
| Public docs articles/videos | IMPLEMENTED | `documentation/` |
| Fake live API endpoint catalog | REMOVED (Phase 0 seed) | Was misleading; replaced with Roadmap articles |
| Architecture/multi-tenant claims in seed | CORRECTED (Phase 0) | Fresh seeds use honest copy |

**Existing databases** seeded before Phase 0 may still contain old documentation records until manually updated or re-seeded.

---

## Infrastructure

| Capability | Status |
|------------|--------|
| Nginx + Gunicorn + systemd deploy templates | IMPLEMENTED |
| Docker Compose (dev) | IMPLEMENTED |
| GitHub Actions CI (tests + checks) | IMPLEMENTED |
| CI/CD auto-deploy to production | NOT IMPLEMENTED |
| Automated DB backups in repo | NOT IMPLEMENTED |

---

## How to use this document

- **Sales/marketing:** Only claim IMPLEMENTED items as live today.
- **Engineering:** Use PLANNED/NOT IMPLEMENTED to prioritize roadmap work.
- **Security/compliance:** Do not represent this repo as a core banking system.

See also: `docs/ZRETA_UPGRADE_ROADMAP.md`, `docs/PHASE_0_COMPLETION_REPORT.md`.
