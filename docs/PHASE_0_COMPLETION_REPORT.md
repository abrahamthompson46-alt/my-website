# Phase 0 — Completion Report

**Date:** 2026-08-13  
**Scope:** Critical security and billing hardening (SEC-002, SEC-001, misleading scope claims)  
**Status:** VERIFIED — 98 tests passing (72 baseline + 26 new)

---

## 1. Original vulnerabilities

| ID | Issue | Severity |
|----|-------|----------|
| SEC-002 / FIN-001 | Checkout accepted client-supplied `amount`/`currency` via POST | HIGH |
| SEC-001 | Payment proofs under `/media/` publicly servable | HIGH |
| Scope | Seed documentation implied live REST API, multi-tenancy, MFI core | MEDIUM |

---

## 2. Root causes

### Checkout manipulation
`CheckoutView.post()` fell through to `request.POST.get("amount")` when no invoice/plan was parsed, and did not validate client price hints when plan/invoice was present. The browser could supply an arbitrary Decimal.

### Public media exposure
Django (`config/urls.py`) and Nginx (`deploy/nginx/marketing-site.conf`) served the entire `MEDIA_ROOT` tree without authentication. `ManualPaymentDetail.proof_document` used `upload_to="payments/proofs/"`.

### Misleading documentation
`seed_documentation.py` created REST API endpoint records and articles describing multi-tenant architecture as if implemented.

---

## 3. Files changed

| File | Change |
|------|--------|
| `payments/services/pricing.py` | **NEW** — server-side checkout pricing resolution |
| `payments/services/checkout.py` | Defense-in-depth `assert_payment_matches_sources()` |
| `payments/views.py` | Removed client amount path; uses pricing service; proof download view |
| `payments/urls.py` | Added `proof_download` route |
| `payments/models/payment.py` | Private upload path for proofs |
| `payments/migrations/0002_alter_manualpaymentdetail_proof_document.py` | **NEW** — records `upload_to` change |
| `core/media_paths.py` | **NEW** — private path detection + upload helper |
| `config/urls.py` | Block public serving of private media paths |
| `deploy/nginx/marketing-site.conf` | Deny `/media/private/` and legacy `/media/payments/proofs/` |
| `templates/payments/payment_detail.html` | Link to authenticated proof download |
| `documentation/management/commands/seed_documentation.py` | Honest roadmap-oriented seed content |
| `payments/tests/test_checkout_security.py` | **NEW** — 18 tests (12 service + 6 view integration) |
| `payments/tests/test_private_media.py` | **NEW** — 7 tests |
| `core/tests/test_media_urls.py` | **Updated** — stricter private-media routing expectations (+1 test) |
| `docs/ZRETA_SCOPE_TRUTH.md` | **NEW** — capability matrix |
| `docs/ZRETA_PHASE_0_DEFERRED.md` | **NEW** — out-of-scope findings |
| `docs/ZRETA_UPGRADE_PROGRESS.md` | Updated Phase 0 statuses |

---

## 4. Exact implementation

### Task 1 — Server-side pricing

**Service:** `resolve_checkout_pricing(user, invoice_id, plan_id, tier_id, posted_amount, posted_currency)`

- Requires **invoice OR plan** (not neither; not both)
- Invoice: must belong to user; status `open`/`overdue`; amount from `Invoice.amount`
- Plan: must be published, not contact-sales; product GA/BETA; tier belongs to plan; amount from `PricingTier.amount`
- If client sends `amount` or `currency`, must **exact match** server authority or `CheckoutPricingError`
- **Removed** free-form amount branch from `CheckoutView`
- **Added** `assert_payment_matches_sources()` in `create_checkout()` as second layer

**Client submits:** `plan_id`, `tier_id`, and/or `invoice_id` only (plus payment method fields).

### Task 2 — Private payment proofs

- Upload path: `private/payments/proofs/` via `private_payment_proof_upload_to()`
- Legacy path `payments/proofs/` treated as private in `is_private_media_path()`
- Public media handler `_serve_public_media()` returns 404 for private paths
- Authenticated download: `GET /app/payments/<uuid>/proof/` — owner or staff only
- Nginx denies direct access to private prefixes (in `deploy/nginx/marketing-site.conf`)

Public marketing assets (e.g. `products/screenshots/`) continue to work.

### Task 3 — Honest scope

- Created `docs/ZRETA_SCOPE_TRUTH.md`
- Rewrote `seed_documentation.py` for fresh installs: Roadmap category replaces fake API catalog

---

## 5. Security impact

| Before | After |
|--------|-------|
| User could POST `amount=1.00` for a GHS 49 plan | Rejected with error; no payment created |
| `/media/private/...` and `/media/payments/proofs/...` publicly reachable | 404 at Django + Nginx (local storage) |
| Proof URL guessable if filename known | Requires auth + payment ownership |
| Docs claimed live `/api/v1/` | Fresh seed uses Roadmap/planned labeling |

---

## 6. Tests

### Baseline
- **72 tests** from pre-Phase 0 — all still passing
- **1 existing test file updated:** `core/tests/test_media_urls.py` (stricter handler expectations; not weakened)

### New tests (26)

#### `payments/tests/test_checkout_security.py` (18)
**Pricing service (12):**
1. Plan checkout resolves server price  
2. Invoice checkout resolves server price  
3. Rejects lower client amount  
4. Rejects higher client amount  
5. Rejects zero client amount  
6. Rejects negative client amount  
7. Rejects precision manipulation (48.50 vs 49.00)  
8. Rejects unknown plan  
9. Rejects tier from other plan  
10. Rejects other user's invoice  
11. Rejects currency mismatch  
12. Rejects missing selection  

**CheckoutView HTTP integration (6):**
13. Normal checkout succeeds with server price  
14. Tampered plan amount rejected in view  
15. Checkout without plan/invoice rejected  
16. Other user's invoice rejected in view (IDOR)  
17. Tampered invoice amount rejected in view  
18. Tampered invoice currency rejected in view  

#### `payments/tests/test_private_media.py` (7)
1. Public route blocks `/media/private/...`  
2. Public route blocks legacy `/media/payments/proofs/...`  
3. Public marketing media route still registered  
4. Owner can download proof  
5. Other user cannot (404)  
6. Unauthenticated redirected  
7. Staff can download  

#### `core/tests/test_media_urls.py` (+1)
- Private media route registered through blocking handler  

---

## 7. Final verification results

```
Command:  DJANGO_SETTINGS_MODULE=config.settings.test python manage.py test
Result:   Ran 98 tests — OK (0 failures, 0 errors)

Command:  python manage.py makemigrations --check
Result:   No changes detected (exit code 0)

Command:  python manage.py check
Result:   System check identified no issues (0 silenced)
```

---

## 8. Migration

**Created:** `payments/migrations/0002_alter_manualpaymentdetail_proof_document.py`

- Single `AlterField` on `ManualPaymentDetail.proof_document`
- Updates Django's recorded `upload_to` callable to `core.media_paths.private_payment_proof_upload_to`
- **Does not** change the database column type
- **Does not** delete or migrate file data on disk
- **Does not** contain unrelated model changes

Existing files on disk keep their current paths until manually moved; HTTP access to legacy public paths is blocked regardless.

---

## 9. Production storage (S3 review)

**Determination: A — Production uses local filesystem storage**

Evidence from repository (not live server inspection):
- `deploy/env/zreta.com.env.example` and `deploy/env/production.vps.env.example` set `MEDIA_URL=/media/` with no `AWS_STORAGE_BUCKET_NAME`
- `deploy/scripts/provision-vps.sh` creates `/var/www/marketing-site/media/`
- Nginx configs alias `/media/` to that local path
- S3 in `config/settings/production.py` is **optional** and only activates when `AWS_STORAGE_BUCKET_NAME` is set

**S3 risk (deferred):** If S3 is enabled later with `AWS_QUERYSTRING_AUTH=False`, Django/Nginx private-path blocking does not apply. Requires bucket policy or signed URLs before enabling S3 for payment proofs. Documented in `docs/ZRETA_PHASE_0_DEFERRED.md`.

**No production-blocking S3 issue** for the documented VPS deployment path.

---

## 10. Legacy payment proofs

| Location | Status |
|----------|--------|
| `media/payments/proofs/` (legacy) | **Not present** in this workspace; HTTP blocked if files exist on production |
| `media/private/payments/proofs/` (new) | Test-run artifacts present locally; HTTP blocked at Django + Nginx |

**Ops note:** Do not delete or auto-move production files. If legacy files exist on VPS under `media/payments/proofs/`, they remain on disk but are blocked at HTTP. Optional maintenance: copy to `media/private/payments/proofs/` and update DB paths.

---

## 11. Deployment requirements

1. **Run migration:** `python manage.py migrate payments`
2. **Nginx:** Reload after pulling — apply deny rules from `deploy/nginx/marketing-site.conf` (also verify `deploy/nginx/zreta.com.conf` gets equivalent deny blocks if that config is active on VPS)
3. **Legacy proofs:** HTTP already blocked; optional file migration during maintenance
4. **Existing documentation DB:** CMS content may still contain pre-Phase-0 fake API records on production DB
5. **No new env vars required** for local-filesystem deployment

---

## 12. Remaining risks (deferred)

Documented in `docs/ZRETA_PHASE_0_DEFERRED.md`:

- Web UI git deploy subprocess (SEC-003)
- Redis session revocation (SEC-005)
- CSP unsafe-inline
- Rate limiting gaps on some POST endpoints
- Product catalog GA statuses vs backend reality
- `create_recurring_checkout` internal amount param (no web exposure)
- S3 private media exposure **if** `AWS_STORAGE_BUCKET_NAME` is enabled without Phase 1 hardening

---

## Stop condition

Phase 0 corrections complete. **Phase 1 not started.** Awaiting explicit approval before commit, push, or deploy.
