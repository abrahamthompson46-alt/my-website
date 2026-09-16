# Zreta Platform — Test Audit

**Audit date:** 2026-08-13  
**Command:** `python manage.py test --settings=config.settings.test --verbosity=2`

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tests** | 72 |
| **Passed** | 72 |
| **Failed** | 0 |
| **Errors** | 0 |
| **Skipped** | 0 |
| **Warnings** | 1 (staticfiles directory missing in local env — non-blocking) |
| **Runtime** | ~8 seconds (SQLite in-memory) |
| **Coverage tool** | ❌ Not configured (`coverage.py` not in requirements) |
| **Coverage percentage** | Not measured |

---

## CI configuration

File: `.github/workflows/ci.yml`

| Step | Status |
|------|--------|
| PostgreSQL 16 service | ✅ |
| Redis 7 service | ✅ |
| `manage.py check --deploy` | ✅ |
| `makemigrations --check --dry-run` | ✅ |
| Full test suite | ✅ |

Note: Tests run with `config.settings.test` (SQLite in-memory), not the CI Postgres service. **Production database parity in tests is partial.**

---

## Test inventory by app

| App | Test file | Approx tests | Focus |
|-----|-----------|--------------|-------|
| accounts | test_auth_flows.py | 8 | Login, logout, MFA, redirects |
| accounts | test_mfa.py | 7 | TOTP, backup codes, URLs |
| accounts | test_team_management.py | 8 | RBAC, invitations, team access |
| accounts | test_invitation_email.py | 3 | Branded email, deliverability |
| common | test_health.py | 1 | Health endpoint |
| common | test_trial_provisioning.py | 1 | Trial subscription |
| common | test_common_tags.py | 2 | Cedi formatting |
| common | test_ui_tags.py | 2 | UI template tags |
| common | test_money.py | 4 | Money utilities |
| control_room | test_views.py | 10 | Control room pages load |
| control_room | test_brand_uploads.py | 3 | Upload validation |
| control_room | test_cache_health.py | 4 | Redis/cache diagnostics |
| control_room | test_navigation_merge.py | 2 | Nav sync |
| control_room | test_platform_ops.py | 4 | Platform ops access, email |
| core | test_media_urls.py | 1 | Media URL routing |
| operations | test_dashboard.py | 1 | Ops dashboard cedi |
| payments | test_webhook_validation.py | 4 | Webhook amount/state validation |
| website | test_homepage.py | 7 | Homepage services and views |

**Total test files:** 18  
**Total test methods:** 72

---

## Areas with adequate test coverage

| Area | Assessment |
|------|------------|
| Authentication flows | ✅ Good |
| MFA (TOTP) | ✅ Good |
| Staff invitations & RBAC | ✅ Good |
| Payment webhook validation | ✅ Good (core scenarios) |
| Control room page smoke tests | ✅ Good |
| Platform ops access control | ✅ Good |
| Homepage upgrade logic | ✅ Good |
| Money/cedi formatting | ✅ Adequate |

---

## Critical gaps — insufficient or missing tests

| Area | Severity | Risk |
|------|----------|------|
| **Checkout amount manipulation** | CRITICAL | No test proving server rejects tampered amounts |
| **Payment portal IDOR** | HIGH | No explicit cross-user payment access tests |
| **Customer portal views** | HIGH | No tests for invoices, tickets, downloads |
| **Refund flows** | HIGH | No refund tests |
| **Manual payment confirmation** | HIGH | Untested |
| **billing_sync (invoice update)** | HIGH | Untested |
| **Session revocation with Redis** | MEDIUM | Untested under cache session backend |
| **Rate limiting** | MEDIUM | Untested |
| **Webhook signature rejection** | MEDIUM | Partial — validation tests mock adapter |
| **Contact/demo form spam** | MEDIUM | Rate limit untested |
| **Partners app** | LOW | No tests |
| **CMS/marketing views** | LOW | Smoke tests only via homepage |
| **Multi-tenancy isolation** | N/A | Not applicable (no tenants) |
| **Loans/savings/ledger** | N/A | Not implemented |
| **API endpoints** | N/A | Not implemented |
| **E2E / browser tests** | LOW | None |
| **Load/performance tests** | LOW | None |

---

## Test settings observations

`config/settings/test.py`:
- SQLite in-memory (fast, not prod-parity)
- MD5 password hasher (fast, insecure — acceptable for tests)
- LocMemCache (rate limit tests may not reflect Redis behavior)
- Debug toolbar removed ✅

---

## Recommendations

### Immediate (before Phase 1)
1. Add `payments/tests/test_checkout.py` — reject client-supplied amounts; enforce tier pricing
2. Add `payments/tests/test_portal_idor.py` — cross-user payment/invoice 404
3. Add `coverage` to CI with minimum threshold (start at 60%, raise over time)

### Short term
4. Integration tests against PostgreSQL in CI (use service container with test settings override)
5. Redis-backed session revocation test
6. Refund and manual payment confirmation tests

### Enterprise upgrade
7. Property-based tests for money/interest calculations (when built)
8. Tenant isolation test suite (when multi-tenancy added)
9. Contract tests for future API

---

## Test execution evidence

```
Ran 72 tests in 7.923s
OK
```

Executed locally on 2026-08-13 with `DJANGO_SETTINGS_MODULE=config.settings.test`.

---

## Coverage estimation (qualitative)

Without coverage.py, estimated coverage by layer:

| Layer | Estimated coverage |
|-------|-------------------|
| accounts/services | ~60% |
| payments/services | ~25% |
| customer_portal | ~5% |
| control_room/views | ~30% (smoke only) |
| marketing/cms/products views | ~5% |
| **Overall codebase** | **~15–25%** (estimate) |

This is insufficient for enterprise fintech but acceptable for current marketing platform scope.
