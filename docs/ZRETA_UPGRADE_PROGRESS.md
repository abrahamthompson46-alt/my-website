# Zreta Platform — Upgrade Progress Tracker

**Last updated:** 2026-09-16 (catalog honesty + CoreTrust request-demo URLs)

Status legend: `NOT STARTED` | `IN PROGRESS` | `IMPLEMENTED` | `VERIFIED` | `PARTIAL` | `CANCELLED`

---

## Phase 1A — Production hardening (sequenced)

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P1A-01 | Remove web-triggered git deploy (SEC-003) | VERIFIED | Commit `055a63f` |
| P1A-02 | Document controlled VPS deployment procedure | VERIFIED | `ZRETA_DEPLOYMENT_PROCEDURE.md` (+ homepage sync step) |
| P1A-03 | Backup & disaster recovery foundation | IMPLEMENTED | Scripts + timer docs ready; **operator must run** `test-restore-drill.sh` once on VPS to mark VERIFIED |

---

## Phase 0 — Audit & immediate fixes

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P0-01 | Complete technical audit | VERIFIED | Docs in `docs/ZRETA_*.md` |
| P0-02 | Run full test suite | VERIFIED | 72 baseline → 98 after Phase 0 corrections |
| P0-03 | Fix checkout amount manipulation | VERIFIED | `payments/services/pricing.py` + 18 checkout tests |
| P0-04 | Secure payment proof uploads | VERIFIED | Private paths + auth download + nginx + migration 0002 |
| P0-05 | Fix Redis session revocation | VERIFIED | `delete_django_session()` uses configured session engine |
| P0-06 | Add checkout IDOR/security tests | VERIFIED | Service + CheckoutView integration tests |
| P0-07 | Add coverage.py to CI | VERIFIED | `requirements/ci.txt` + coverage fail-under in CI |
| P0-08 | Sanitize health endpoint errors | VERIFIED | Completed in production hardening pass |
| P0-09 | Honest scope documentation | VERIFIED | `ZRETA_SCOPE_TRUTH.md` + seed_documentation + `/legal/enterprise/` |

---

## Phase 1 — Production hardening

| ID | Task | Status |
|----|------|--------|
| P1-01 | Server-side pricing enforcement | VERIFIED | Completed in Phase 0 |
| P1-02 | Private media / signed URLs | PARTIALLY IMPLEMENTED | Phase 0 (local FS + auth views); S3 signed URLs Phase 1+ |
| P1-03 | Payment audit events | VERIFIED | `payments/services/payment_audit.py` |
| P1-04 | Universal POST rate limiting | VERIFIED | Public rate limits for checkout/contact/newsletter/webhooks |
| P1-05 | CI/CD deploy (remove web git pull) | VERIFIED | Phase 1A.1 — web deploy removed; full CI/CD optional Phase 1+ |
| P1-06 | Automated DB + media backups | IN PROGRESS | Phase 1A.2 scripts; restore drill pending |
| P1-07 | PostgreSQL SSL + statement_timeout | VERIFIED | `DB_SSLMODE` + `DB_STATEMENT_TIMEOUT_MS` in production settings |
| P1-08 | CSP tightening (remove unsafe-inline) | VERIFIED | script-src no longer allows unsafe-inline; styles deferred |
| P1-09 | PostgreSQL integration tests in CI | VERIFIED | `CI_USE_POSTGRES=1` in GitHub Actions |
| P1-10 | Append-only audit log | VERIFIED | Model + queryset guards; admin delete disabled |
| P1-11 | Payment row locking (select_for_update) | VERIFIED | Webhooks, verify, manual confirm, refunds |
| P1-12 | Refund integration tests | VERIFIED | `payments/tests/test_refunds.py` |

---

## Phase 2 — Platform architecture

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P2-01 | Tenant model (Organization, Membership) | VERIFIED | `organizations` app + backfill migration |
| P2-02 | Tenant resolution middleware | VERIFIED | `ActiveOrganizationMiddleware` + session switch |
| P2-03 | Tenant-scoped querysets | VERIFIED | Org FK + scoping on subscriptions/licenses/invoices/payments/tickets/downloads/notifications |
| P2-04 | DRF API v1 | VERIFIED | `/api/v1/` token auth + org header scoping |
| P2-05 | API authentication | VERIFIED | DRF Token (+ session) authentication |
| P2-06 | Celery/async jobs | VERIFIED | Celery + Redis broker; `docs/CELERY.md` |
| P2-07 | Async email + webhooks | VERIFIED | `queue_platform_mail` + `enqueue_process_webhook` |
| P2-08 | Structured logging + shipping | VERIFIED | JSON logs + request_id; `docs/OBSERVABILITY.md` |
| P2-09 | Prometheus metrics | VERIFIED | Token-gated `/metrics/`; HTTP/webhook/email series |
| P2-10 | API rate limiting and versioning | VERIFIED | DRF throttles + `/api/v1` namespace |

---

## Phase 3 — In-repo MFI financial core

**CANCELLED (2026-09-14).** CoreTrust is already built and deployed as a separate product. This website markets and bills it; it does not re-implement banking.

Brief experimental `ledger` / `clients` apps were removed. See `docs/ZRETA_PRODUCT_MODEL.md`.

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P3-01…P3-18 | In-repo GL, EOD, borrowers, loans, savings, etc. | CANCELLED | Belongs in CoreTrust, not this repo |

---

## Phase 4 — External product integration

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P4-01 | CoreTrust catalog + external app links | IMPLEMENTED | Product rename + `micro.zreta.com` URLs |
| P4-02 | ChurchHub portal ↔ app provisioning | NOT STARTED | — |
| P4-03 | CoreTrust / ChurchHub portal launch CTAs | IMPLEMENTED | Dashboard/subscriptions/licenses Launch app for active entitlements |
| P4-04 | Unified identity across product apps | NOT STARTED | — |
| P4-05 | Cross-product billing refinements | NOT STARTED | — |

---

## Verification gates

| Gate | Criteria | Status |
|------|----------|--------|
| G0 | Audit docs approved by stakeholder | IN PROGRESS |
| G1 | Phase 0 fixes deployed + tested | VERIFIED (local: 98 tests, migration check, security review) |
| G2 | Coverage ≥ 55% on accounts/payments/common/core (CI gate) | VERIFIED | coverage fail-under=55 in CI |
| G3 | Tenant isolation tests pass | VERIFIED | `organizations/tests/test_tenancy.py` |
| G4 | In-repo MFI ledger trial balance | CANCELLED | CoreTrust is external; gate retired |

---

## Change log

| Date | Event |
|------|-------|
| 2026-08-13 | Initial audit completed |
| 2026-08-13 | Phase 0 security fixes implemented (95 tests) |
| 2026-08-13 | Phase 0 final corrections: migration 0002, view-level checkout tests, docs (98 tests) |
| 2026-08-13 | Phase 1A.1 started: web deploy removed, deployment procedure documented |
| 2026-08-13 | Phase 1A.1 verified: nginx private-media deny rules in zreta.com.conf (102 tests) |
| 2026-08-13 | Phase 1A.2 started: backup/restore scripts and DR documentation |
| 2026-09-14 | Phase 2.6–2.7: Celery workers, async email + webhook enqueue |
| 2026-09-14 | Phase 2.8–2.9: JSON structured logging + Prometheus `/metrics/` |
| 2026-09-14 | Phase 3.1–3.4 briefly added in-repo ledger/clients (later reversed) |
| 2026-09-14 | Product model realigned: storefront + external CoreTrust; Phase 3 cancelled; `ledger`/`clients` removed |
| 2026-09-15 | Portal Launch app CTAs for active ChurchHub/CoreTrust subscriptions |
| 2026-09-16 | Website assessment + implementation plan added (`docs/ZRETA_WEBSITE_ASSESSMENT_AND_PLAN.md`) |

---

## Website credibility & growth (from assessment)

Master plan: [ZRETA_WEBSITE_ASSESSMENT_AND_PLAN.md](ZRETA_WEBSITE_ASSESSMENT_AND_PLAN.md)

| ID | Task | Status | Notes |
|----|------|--------|-------|
| W1-01 | Trial length consistency (30 days) | DONE | Public templates + pricing use 30-day; refund 14-day window kept |
| W1-02 | Pricing currency clarity (GHS/USD) | DONE | Currency labelled on pricing cards + footnotes |
| W1-03 | CoreTrust naming only in public UI | DONE | Sanitize + sync; public UI CoreTrust |
| W1-04 | Remove unproven trust slogans | DONE | About/hero/support rewrite; placeholder team filtered |
| W1-05 | Hide empty Case Studies / Success Stories | DONE | Removed from primary nav + marketing hub + sitemap |
| W1-06 | About/Company facts page | DONE | Facts-first About + sync_homepage about repair |
| W1-07 | Security Center v1/v2 | DONE | Hub links + auth/encryption/disclosure |
| W1-08 | Support Center v1 | DONE | `/support/` entry with docs/tickets/status/SLA |
| W1-09 | Live / Early Access / Coming soon badges | DONE | Product cards + solution landings |
| W2-01 | Homepage hero conversion rewrite | DONE | Brand-first hero; Products + Request demo CTAs |
| W2-02 | Product cards scannable | DONE | Status badge + one outcome + CTA |
| W2-05 | CTA consistency | DONE | Outbound chooser + solution CTAs |
| W2-06 | Industry solution landing pages | DONE | `/solutions/*` |
| W2-07 | Pricing polish | DONE | Monthly/annual + currency + SLA link |
| W2-08 | Slim primary navigation | DONE | Products \| Solutions \| Platform \| Resources \| Pricing |
| W3-01 | First verified customer story | DEFERRED | Keep Customers/stories hidden until verified |
| W3-03 | Platform architecture page | DONE | `/platform/architecture/` |
| W3-04 | Security Center depth | DONE | Linked from footer + platform nav |
| W3-05 | API/integrations honesty | DONE | `/platform/integrations/` |
| W3-07 | Product page depth templates | DONE | ChurchHub + CoreTrust depth sections |
| W4-01 | Enterprise onboarding page | DONE | `/platform/onboarding/` |
| W4-02 | SLA documentation | DONE | `/platform/sla/` |
| W4-03 | Privacy Center | DONE | `/platform/privacy/` |
| W4-04 | Business continuity summary | DONE | `/platform/continuity/` |
| W4-07 | Status page component list | DONE | External products labelled; no fake uptime charts |
| W5-01 | Soft-close empty case studies / success stories | DONE | Redirect to Resources hub when empty |
| W5-02 | Outbound trial/demo funnel instrumentation | DONE | `/go/<slug>/<intent>/` + Ops Analytics |
| W6-01 | Evidence-led “What you can verify” | DONE | Replaces “Why teams trust Zreta” |
| W6-02 | Reliability page for enterprise claim | DONE | `/platform/reliability/` |
| W6-03 | Security Center TOC expansion | DONE | Auth → disclosure map |
| W6-04 | Unpublish Hospital 2.0 contradiction | DONE | sync + seed rewrite |
| W6-05 | Nav Live vs Coming soon labels | DONE | Product mega menu |
| W6-06 | Product status badges on detail | DONE | Live / Early access / Coming soon |
| W6-07 | Homepage CTA de-duplication | DONE | Removed how-it-works + bottom CTA |

**Still deferred (needs real assets/people):** customer logos, verified counts, screenshots/product tours, case studies, CoreTrust CTF rebrand (cross-repo), VPS deploy.

