# Zreta Platform — Security Audit

**Audit date:** 2026-08-13  
**Scope:** Authentication, authorization, input validation, headers, secrets, uploads, payments

---

## Summary

The platform demonstrates **mature baseline security for a Django marketing/SaaS portal**: staff MFA, production settings validation, CSRF on forms, webhook signature verification, auth rate limiting, and audit logging. 

**Critical gaps for an enterprise fintech upgrade:** no multi-tenant isolation, public media exposure for sensitive uploads, checkout amount manipulation, and deploy subprocess execution from the web UI.

---

## Findings register

### SEC-001 — Public `/media/` may expose sensitive uploads

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **Location** | `config/urls.py:31-46`, `deploy/nginx/marketing-site.conf:72-77`, `payments/models/payment.py:148` |
| **What** | User uploads (payment proofs, avatars, CMS assets) served without authentication |
| **Why it matters** | Payment proof documents may contain bank details; predictable paths could leak PII |
| **Evidence** | Nginx `location /media/` with public alias; Django serves media when `FileSystemStorage` even with DEBUG=False |
| **Recommended solution** | Private object storage with signed URLs; or authenticated download views for sensitive paths |
| **Dependencies** | S3 migration, storage backend refactor |
| **Complexity** | Medium (2–3 weeks) |

---

### SEC-002 — Checkout accepts client-supplied payment amount

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **Location** | `payments/views.py:145-154` |
| **What** | If no invoice/plan selected, `amount` and `currency` taken from POST body |
| **Why it matters** | Authenticated user could pay arbitrary low amount for subscription-priced products |
| **Evidence** | `amount = Decimal(str(raw_amount))` without server-side price validation |
| **Recommended solution** | Require invoice or pricing_tier; reject free-form amount; server-side price lookup only |
| **Dependencies** | Checkout form UX change |
| **Complexity** | Low (1–2 days) |

---

### SEC-003 — Platform Ops GitHub deploy executes shell commands

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **Location** | `control_room/services/deploy.py:18-51` |
| **What** | `subprocess.run` for `git fetch`, `git pull`, `migrate`, `collectstatic` triggered from web UI |
| **Why it matters** | Compromised platform-owner session = arbitrary command execution as app user; no rollback automation |
| **Evidence** | `_run_command(["git", "pull", remote, branch])` etc. |
| **Recommended solution** | Move deploy to CI/CD webhook or separate deploy agent; remove subprocess from request cycle |
| **Dependencies** | GitHub Actions, deploy tokens |
| **Complexity** | Medium |

---

### SEC-004 — CSP permits unsafe-inline scripts and styles

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Location** | `config/settings/base.py:356-363` |
| **What** | `script-src 'self' 'unsafe-inline'` and `style-src 'self' 'unsafe-inline'` |
| **Why it matters** | Inline script XSS would not be blocked by CSP |
| **Evidence** | SECURITY_CSP dict |
| **Recommended solution** | Nonce-based CSP; extract inline scripts; tighten gradually |
| **Dependencies** | Template refactor |
| **Complexity** | Medium–High |

---

### SEC-005 — Session revocation incompatible with Redis cache sessions

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Location** | `accounts/services/sessions.py:59-74`, `config/redis_settings.py` |
| **What** | Revocation deletes DB `Session` rows; production uses `cached_db` or cache session engine |
| **Why it matters** | "Revoke other sessions" may not invalidate active Redis-backed sessions |
| **Evidence** | `Session.objects.filter(session_key=...).delete()` only |
| **Recommended solution** | Use cache.delete(session_key) for cache backend; verify with integration test under Redis |
| **Dependencies** | Redis session config |
| **Complexity** | Low |

---

### SEC-006 — Nginx X-Frame-Options conflicts with Django

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Location** | `deploy/nginx/marketing-site.conf:53` vs `base.py:348` |
| **What** | Nginx sets `X-Frame-Options: SAMEORIGIN`; Django middleware sets `DENY` |
| **Why it matters** | Inconsistent framing policy; Nginx may override depending on header order |
| **Evidence** | Both configs present |
| **Recommended solution** | Align on DENY everywhere unless embedding required |
| **Complexity** | Trivial |

---

### SEC-007 — Health endpoint may leak infrastructure errors

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Location** | `core/views.py:25-27, 38-39` |
| **What** | Database/cache exception strings returned in JSON on failure |
| **Why it matters** | Information disclosure to unauthenticated callers |
| **Evidence** | `"database": str(exc)` |
| **Recommended solution** | Generic error messages publicly; detailed logs server-side |
| **Complexity** | Trivial |

---

### SEC-008 — Webhook endpoint CSRF-exempt (expected, mitigated)

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL |
| **Location** | `payments/views.py:234-254` |
| **What** | CSRF exempt on webhook POST |
| **Why it matters** | Required for provider callbacks; must rely on signature verification |
| **Evidence** | `@csrf_exempt`; `adapter.verify_webhook()` in `payments/services/webhooks.py:21` |
| **Recommended solution** | Maintain signature verification; add IP allowlisting if providers publish ranges |
| **Complexity** | Low |

---

### SEC-009 — No CORS configuration

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL |
| **Location** | Settings |
| **What** | No `django-cors-headers` — server-rendered site only |
| **Why it matters** | Not a current risk; required if API added |
| **Evidence** | No CORS in INSTALLED_APPS |
| **Recommended solution** | Add explicit CORS when building API |
| **Complexity** | N/A today |

---

### SEC-010 — Rate limiting not universal

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Location** | `accounts/services/rate_limit.py`, `common/services/demo_requests.py` |
| **What** | Rate limits on auth and demo forms; not on checkout, webhooks, contact, newsletter |
| **Why it matters** | Abuse/spam on unprotected POST endpoints |
| **Evidence** | Grep shows limited scopes |
| **Recommended solution** | Extend rate limits to all public POST endpoints; use Redis in prod |
| **Complexity** | Low–Medium |

---

### SEC-011 — Audit log not tamper-evident

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Location** | `accounts/models/audit.py` |
| **What** | AuditLog is a normal mutable model; staff with DB access can alter |
| **Why it matters** | Compliance requirements often need append-only audit trails |
| **Evidence** | No `save()` override preventing updates; admin may expose records |
| **Recommended solution** | Append-only pattern, DB permissions, or external SIEM |
| **Complexity** | Medium |

---

### SEC-012 — Superuser bypass on all RBAC

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL |
| **Location** | `accounts/services/rbac.py` |
| **What** | `is_superuser` returns True for all permission checks |
| **Why it matters** | Standard Django; limit superuser count in production |
| **Evidence** | Lines 13-14, 43-44 |
| **Recommended solution** | Break-glass superuser policy; MFA required (already for staff) |
| **Complexity** | Process |

---

## Category assessment

| Category | Status | Notes |
|----------|--------|-------|
| Authentication bypass | ✅ No evidence | Lockout + MFA for staff |
| Authorization bypass | ⚠️ Partial | User scoping good; no object-level perms; checkout amount issue |
| IDOR | ✅ Mostly mitigated | `UserQuerysetMixin`, `get_object_or_404(..., user=request.user)` |
| Cross-tenant leakage | N/A | No tenants — see multitenancy audit |
| Privilege escalation | ⚠️ Low risk | RBAC tested; superuser is main path |
| CSRF | ✅ Forms protected | Webhooks exempt by design |
| XSS | ⚠️ Partial | Django auto-escape; CSP weakened by unsafe-inline |
| SQL injection | ✅ Low risk | ORM used; no raw SQL in views reviewed |
| Insecure file uploads | ⚠️ HIGH | Public media + payment proofs |
| Insecure session config | ⚠️ MEDIUM | Redis revocation gap |
| Weak passwords | ✅ Validators present | Django validators + lockout |
| Exposed secrets | ✅ None in repo | Env-based |
| Unsafe API endpoints | N/A | No public API |
| Missing rate limiting | ⚠️ MEDIUM | Partial coverage |
| Insecure CORS | N/A | No API |
| Insecure cookies | ✅ Production secure flags | HttpOnly, Secure, SameSite |
| Missing security headers | ✅ Good baseline | CSP, COOP, CORP, Referrer-Policy |
| Unsafe redirects | ✅ Mitigated | Login redirect tests exist |
| Sensitive info leakage | ⚠️ LOW | Health endpoint, public media |

---

## IDOR trace (customer portal)

| Resource | Scoping mechanism | Verdict |
|----------|-------------------|---------|
| Payments | `filter(user=request.user)` | ✅ |
| Invoices | `UserQuerysetMixin` | ✅ |
| Tickets | `UserQuerysetMixin` | ✅ |
| Notifications | `get_object_or_404(..., user=request.user)` | ✅ |
| Licenses | `UserQuerysetMixin` | ✅ |
| Downloads | `UserQuerysetMixin` | ✅ |

**Malicious user manipulating UUID in URL:** Django `DetailView` + scoped queryset returns 404 — **no IDOR found in portal views reviewed**.

---

## What must NOT be weakened during upgrade

- Production SECRET_KEY / ALLOWED_HOSTS / CSRF validation
- Staff MFA middleware
- Webhook signature verification
- Email verification gate on customer portal
- Payment webhook amount/currency validation (`payments/services/webhooks.py:87-103`)
