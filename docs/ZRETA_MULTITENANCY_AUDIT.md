# Zreta Platform — Multi-Tenancy Audit

**Audit date:** 2026-08-13  
**Verdict:** **Multi-tenancy is NOT implemented.** The platform uses **single-tenant architecture with per-user data isolation**.

---

## Executive summary

A malicious authenticated user **cannot access another organization's data via ID manipulation** because there are no organizations — only individual user accounts. However, this also means the platform **cannot support** multi-organization SaaS (e.g., one MFI tenant with many staff users sharing loan books) without a major schema and application redesign.

Marketing and documentation content **incorrectly implies** multi-tenant architecture (`documentation/seed_documentation.py` references "multi-tenant design" and `/api/v1/users` in organization context).

---

## Tenant isolation model (as-is)

```
┌─────────────────────────────────────────┐
│           Single Zreta Platform          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │ User A  │  │ User B  │  │ Staff   │  │
│  │ portal  │  │ portal  │  │ ops     │  │
│  └────┬────┘  └────┬────┘  └────┬────┘  │
│       │            │            │        │
│       ▼            ▼            ▼        │
│   filter(user=A) filter(user=B) RBAC     │
└─────────────────────────────────────────┘
```

---

## Trace matrix

| Layer | Tenant mechanism | Evidence | Cross-user access risk |
|-------|------------------|----------|------------------------|
| **Models** | `ForeignKey(User)` | `payments.Payment.user`, `customer_portal.Invoice.user` | None at model level |
| **Managers** | None custom | Default managers | No automatic tenant filter |
| **Querysets** | Manual `filter(user=)` | `UserQuerysetMixin`, payment views | LOW if mixin used |
| **Views** | LoginRequired + scoping | `customer_portal/views.py` | LOW — verified IDOR-safe |
| **APIs** | N/A | No REST API | N/A |
| **Serializers** | N/A | — | N/A |
| **Services** | User passed explicitly | `get_dashboard_stats(user)` | Depends on caller |
| **Reports** | Staff see all data | `operations/services/dashboard.py` | By design for staff |
| **Exports** | Not implemented | — | N/A |
| **Background tasks** | None | — | N/A |
| **Notifications** | `user` FK scoped | `PortalNotification` | LOW |
| **Caching** | User-agnostic keys for public pages | `@cache_page` on homepage | Public content only |
| **File storage** | Path-based, no tenant prefix | `upload_to="payments/proofs/"` | **HIGH** — public URLs |

---

## Isolation mechanisms in code

### Customer portal (`customer_portal/mixins.py`)

```python
class UserQuerysetMixin:
    user_field = "user"
    def get_queryset(self):
        return super().get_queryset().filter(**{self.user_field: self.request.user})
```

Used by: Subscriptions, Licenses, Invoices, Downloads, Tickets, Notifications.

### Payments (`payments/views.py`)

```python
Payment.objects.filter(user=self.request.user)
get_object_or_404(Invoice, pk=invoice_id, user=request.user)
get_object_or_404(Payment, reference=reference, user=request.user)
```

### Staff areas

Staff with `/ops/` or `/control/` access can view **platform-wide** data (all demo requests, all payments in ops dashboard). This is intentional operator access, not a tenant leak.

---

## Attack scenario analysis

### Scenario 1: Customer A accesses Customer B's invoice

**Steps:** Authenticated as User A, request `/app/invoices/<uuid-of-B-invoice>/`

**Result:** `UserQuerysetMixin` queryset excludes B's invoice → **404 Not Found**

**Verdict:** ✅ Mitigated

### Scenario 2: Customer manipulates payment reference

**Steps:** Access `/app/payments/return/<reference>/` with another user's reference

**Result:** `get_object_or_404(Payment, reference=reference, user=request.user)` → **404**

**Verdict:** ✅ Mitigated

### Scenario 3: Customer accesses another user's payment proof document

**Steps:** Guess `/media/payments/proofs/<filename>`

**Result:** Nginx serves file without auth if URL known

**Verdict:** ❌ **Vulnerable** (public media, not tenant/user scoped at storage layer)

### Scenario 4: Staff user escalates to platform owner

**Steps:** Manipulate role assignment without authorization

**Result:** Role assignment requires `TeamManagementMixin` (platform-owner/admin)

**Verdict:** ✅ Mitigated (tested in `test_team_management.py`)

### Scenario 5: Cross-tenant API access

**Steps:** Call `/api/v1/users`

**Result:** Route does not exist

**Verdict:** N/A — API not implemented

---

## What "organization" means in this codebase

| Context | Meaning |
|---------|---------|
| User profile `company` field | Free-text label on forms |
| SEO schema `Organization` | JSON-LD for search engines |
| Marketing copy | Industry vertical (faith org, MFI) |
| Seed documentation | Aspirational/future architecture |

**There is no `Organization` model, no `tenant_id`, no row-level security policy.**

---

## Implications for enterprise upgrade

To support true multi-tenancy (required for Microfinance Core):

| Component | Required change | Complexity |
|-----------|-----------------|------------|
| Data model | Add `Organization`, `OrganizationMembership`, tenant FK on all business tables | High |
| Middleware | Tenant resolution from subdomain/header/session | Medium |
| Querysets | Tenant-aware manager or django-tenants schema | High |
| RBAC | Organization-scoped roles | High |
| File storage | Tenant-prefixed paths + auth | Medium |
| Cache keys | Tenant prefix | Low |
| Background jobs | Tenant context propagation | Medium |
| Reports | Tenant-scoped aggregations | High |
| Audit | Tenant ID on all events | Medium |

---

## Recommendations

1. **Do not claim multi-tenancy** in product/docs until implemented
2. **Immediate:** Secure sensitive uploads (payment proofs) — not a tenancy fix but related isolation failure
3. **Phase 1 upgrade:** Design tenant model before any loan/ledger work
4. **Choose strategy:** Schema-per-tenant vs shared-schema with `tenant_id` — decision required before implementation

---

## Risk summary

| Risk | Severity |
|------|----------|
| Cross-user IDOR in portal views | LOW (well scoped) |
| Cross-tenant data leakage | N/A (no tenants) |
| Public media exposure | HIGH |
| Staff over-broad data access | MEDIUM (by design; needs audit for future tenants) |
| Future tenant implementation debt | CRITICAL for fintech roadmap |
