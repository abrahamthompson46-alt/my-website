# Zreta Platform — Upgrade Progress Tracker

**Last updated:** 2026-08-13 (Phase 1A.2 in progress)

Status legend: `NOT STARTED` | `IN PROGRESS` | `IMPLEMENTED` | `VERIFIED`

---

## Phase 1A — Production hardening (sequenced)

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P1A-01 | Remove web-triggered git deploy (SEC-003) | VERIFIED | Commit `055a63f` |
| P1A-02 | Document controlled VPS deployment procedure | VERIFIED | `ZRETA_DEPLOYMENT_PROCEDURE.md` |
| P1A-03 | Backup & disaster recovery foundation | IN PROGRESS | Scripts + docs; restore drill pending VPS |

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

All items: **NOT STARTED**

---

## Phase 3 — Financial core (MFI)

All items: **NOT STARTED**

---

## Phase 4 — Product integration

All items: **NOT STARTED**

---

## Verification gates

| Gate | Criteria | Status |
|------|----------|--------|
| G0 | Audit docs approved by stakeholder | IN PROGRESS |
| G1 | Phase 0 fixes deployed + tested | VERIFIED (local: 98 tests, migration check, security review) |
| G2 | Coverage ≥ 55% on accounts/payments/common/core (CI gate) | VERIFIED | coverage fail-under=55 in CI |
| G3 | Tenant isolation tests pass | NOT STARTED |
| G4 | MFI ledger trial balance balances | NOT STARTED |

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
