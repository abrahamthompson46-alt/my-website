# Zreta Platform — Enterprise Upgrade Roadmap

**Audit date:** 2026-08-13  
**Updated:** 2026-09-14  
**Baseline:** Marketing/CMS + customer billing platform  
**Target:** Enterprise-grade multi-product **storefront** (catalog, portal, billing, tenancy) that sells external products such as ChurchHub and CoreTrust

---

## Phase 0 — Audit & stabilization

| Task | Priority | Complexity |
|------|----------|------------|
| Complete technical audit | P0 | Done |
| Fix checkout amount manipulation | P0 | Low |
| Secure payment proof uploads | P0 | Medium |
| Fix Redis session revocation | P1 | Low |
| Add payment/checkout IDOR tests | P1 | Low |
| Add coverage.py to CI | P1 | Low |
| Remove/replace misleading API docs in seed | P2 | Low |

---

## Phase 1 — Production hardening (4–6 weeks)

**Goal:** Make current marketing + billing platform enterprise-operable.

| # | Work item | Complexity |
|---|-----------|------------|
| 1.1 | Enforce server-side pricing on all checkout paths | Low |
| 1.2 | Private media storage (S3 + signed URLs for sensitive paths) | Medium |
| 1.3 | Payment audit events | Low |
| 1.4 | Extend rate limiting to contact, newsletter, checkout | Low |
| 1.5 | Remove web-triggered git deploy; CI/CD deploy pipeline | Medium |
| 1.6 | Automated PostgreSQL + media backups | Medium |
| 1.7 | DB SSL + statement_timeout | Low |
| 1.8 | Tighten CSP | Medium |
| 1.9 | PostgreSQL integration tests in CI | Low |
| 1.10 | Health endpoint error sanitization | Trivial |
| 1.11 | Append-only audit log pattern | Medium |
| 1.12 | `select_for_update` on payment status transitions | Low |

---

## Phase 2 — Platform architecture (6–10 weeks)

**Goal:** API layer, async jobs, observability, tenant foundation.

| # | Work item | Complexity |
|---|-----------|------------|
| 2.1 | Tenant model (Organization, Membership) | High |
| 2.2 | Tenant resolution middleware | High |
| 2.3 | Tenant-scoped querysets/managers | High |
| 2.4 | Django REST Framework API v1 | High |
| 2.5 | API authentication | Medium |
| 2.6 | Celery + Redis task queue | Medium |
| 2.7 | Async email and webhook processing | Medium |
| 2.8 | Structured logging + log shipping | Medium |
| 2.9 | Prometheus metrics / Grafana | Medium |
| 2.10 | API rate limiting and versioning | Medium |
| 2.11 | Tenant isolation test suite | Medium |

---

## Phase 3 — In-repo MFI financial core — CANCELLED

**Decision (2026-09-14):** Do **not** build banking/GL/loans inside this repository.

**CoreTrust** is already built, deployed, and functioning as the MFI product. This site markets and bills it (same pattern as ChurchHub).

Former Phase 3 items (chart of accounts, journals, EOD, borrowers, loans, savings, etc.) belong in the **CoreTrust codebase**, not here.

See `docs/ZRETA_PRODUCT_MODEL.md`.

---

## Phase 4 — External product integration (primary product roadmap)

| # | Work item | Complexity |
|---|-----------|------------|
| 4.1 | Honest catalog + external links for ChurchHub and CoreTrust | Low |
| 4.2 | ChurchHub tenant provisioning from marketing site | Medium |
| 4.3 | CoreTrust portal launch / license sync | Medium |
| 4.4 | Unified identity across product subdomains | High |
| 4.5 | Cross-product billing refinements | High |
| 4.6 | ERP/School/Hospital modules (separate products when ready) | Very High each |

---

## Recommended upgrade order

1. **Phase 0–1** — harden marketing + billing platform  
2. **Phase 2** — tenancy, API, async, observability  
3. **Phase 4** — deeper integration with external products (ChurchHub, CoreTrust)  
4. **Do not resume in-repo MFI core** — use CoreTrust  

---

## Architecture decision (resolved)

| Option | Status |
|--------|--------|
| Build MFI engine inside this monolith | **Rejected** |
| CoreTrust as separate live product; this site is storefront | **Accepted** |
| Shared-schema org tenancy for portal/billing | **Accepted** (Phase 2) |

---

## What should NOT be changed

- Production settings validation (SECRET_KEY, ALLOWED_HOSTS, CSRF, Redis requirement)
- Staff MFA enforcement
- Webhook signature verification logic
- Separation of CoreTrust (and ChurchHub) as external apps
- Existing passing test suite (extend, don't weaken)

---

## Estimated total complexity

| Scope | Duration (est.) | Team |
|-------|-----------------|------|
| Phase 0–1 (hardening) | 4–6 weeks | 1–2 engineers |
| Phase 2 (platform) | 6–10 weeks | 2–3 engineers |
| Phase 3 (in-repo MFI) | — | **Cancelled** |
| Phase 4 (external product integration) | Ongoing | Variable |

**This repository’s job:** sell and support products. **CoreTrust’s job:** run microfinance.

See `ZRETA_UPGRADE_PROGRESS.md` and `ZRETA_PRODUCT_MODEL.md`.
