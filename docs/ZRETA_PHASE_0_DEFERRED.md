# Phase 0 — Deferred Items

**Date:** 2026-08-13

Issues discovered during Phase 0 that are **out of scope** for this phase. Left unchanged intentionally.

---

## SEC-003 — Web UI git deploy subprocess

**Location:** `control_room/services/deploy.py`  
**Severity:** HIGH  
**Reason deferred:** Not one of the three Phase 0 fixes; requires CI/CD design (Phase 1).

---

## SEC-005 — Redis session revocation gap

**Location:** `accounts/services/sessions.py`  
**Severity:** MEDIUM  
**Reason deferred:** Phase 1 hardening item; not part of checkout/media/scope tasks.

---

## Existing documentation database records

**Issue:** VPS/production databases seeded before Phase 0 may still contain:
- Fake `/api/v1/*` endpoint records
- "Multi-tenant architecture" article copy

**Reason deferred:** Phase 0 updated `seed_documentation.py` for fresh installs only. Existing DB requires manual CMS update or a future `sync_documentation_scope` command (Phase 1).

---

## Legacy payment proofs at `media/payments/proofs/`

**Issue:** Files uploaded before Phase 0 may remain at the legacy public path on disk.

**Mitigation applied:** Django and Nginx now block ` /media/payments/proofs/` and `/media/private/`.  
**Remaining action:** Migrate legacy files to private path or remove from public disk during deploy (ops task).

---

## CSP `unsafe-inline`

**Location:** `config/settings/base.py`  
**Severity:** MEDIUM  
**Reason deferred:** Phase 1 security hardening.

---

## Rate limiting on checkout/contact/newsletter

**Severity:** MEDIUM  
**Reason deferred:** Phase 1 item.

---

## Product catalog statuses for non-ChurchHub modules

**Issue:** `seed_products.py` still marks several modular products as `GA` for marketing catalog purposes.

**Reason deferred:** Changing live product statuses could affect public product pages without explicit product owner approval. Scope truth document clarifies backend reality. Status alignment deferred to product/content review.

---

## create_recurring_checkout amount parameter

**Location:** `payments/services/checkout.py`  
**Issue:** Internal function accepts caller-supplied amount (not exposed via web views today).

**Reason deferred:** No web entry point; address when recurring billing UI is built.

---

## S3 media storage — private payment proofs (conditional)

**Location:** `config/settings/production.py` (optional `AWS_STORAGE_BUCKET_NAME`)  
**Severity:** HIGH **if S3 is enabled without bucket policy or signed URLs**

**Current production configuration (repo evidence):**
- VPS env templates (`deploy/env/zreta.com.env.example`, `deploy/env/production.vps.env.example`) use local `MEDIA_URL=/media/` and do **not** set `AWS_STORAGE_BUCKET_NAME`.
- Deploy scripts provision `/var/www/marketing-site/media/` and Nginx serves media from disk.
- **Conclusion:** Documented production path uses **local filesystem storage**.

**Risk when S3 is enabled:** Django `_serve_public_media()` and Nginx deny rules do not apply; `AWS_QUERYSTRING_AUTH=False` may expose objects at direct CDN URLs.

**Reason deferred:** Production does not use S3 per repo configuration. Address in Phase 1 before enabling S3 (signed URLs, private bucket prefix policy, or separate private bucket).
