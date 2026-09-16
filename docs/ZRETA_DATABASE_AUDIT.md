# Zreta Platform — Database Audit

**Audit date:** 2026-08-13  
**Engine:** PostgreSQL 16 (production), SQLite in-memory (tests)

---

## Schema overview

### Core identity (`accounts`)
| Model | Key fields | Relationships |
|-------|------------|---------------|
| User | UUID PK, email, is_staff | AUTH_USER_MODEL |
| UserSecurityProfile | MFA secrets, lockout, email_verified | OneToOne → User |
| UserSession | session_key, IP, revoked_at | FK → User |
| Role, UserRole | slug, permissions M2M | RBAC |
| StaffInvitation | token hash, expiry | Team onboarding |
| AuditLog | event_type, metadata JSON | FK → User (nullable) |

### Commerce (`customer_portal`, `payments`, `products`)
| Model | Purpose |
|-------|---------|
| Product, PricingPlan, PricingTier | Catalog |
| Subscription, License, Invoice | Customer billing state |
| Payment, PaymentAttempt, Refund | Payment collection |
| WebhookEvent, RecurringPayment | Gateway integration |
| ManualPaymentDetail | Offline payment proofs |
| ProductDemoRequest | Sales leads |

### Content (`cms`, `marketing`, `documentation`)
| Model | Purpose |
|-------|---------|
| CMSPage, PageSection, SectionItem | Homepage/About CMS |
| HeroBanner, Testimonial, NewsArticle | Marketing content |
| BlogPost, Event, NewsletterSubscriber | Marketing |
| DocArticle, DocVideo, DocDownload | Help center |

### Platform (`control_room`)
| Model | Purpose |
|-------|---------|
| PlatformSettings | Site config, feature flags |
| NavigationItem, BrandAsset | UI configuration |

---

## Relationships diagram (simplified)

```
User ──┬── Subscription ── Product
       ├── Invoice ── Payment
       ├── License
       ├── SupportTicket ── TicketMessage
       ├── PortalNotification
       ├── CustomerDownload
       └── Payment ── GatewayConfiguration
                    ├── WebhookEvent
                    ├── Refund
                    └── ManualPaymentDetail
```

**No Organization/Tenant entity exists.**

---

## Indexes and constraints

### Present (evidence from models/migrations)

| Table | Index/Constraint | Purpose |
|-------|-------------------|---------|
| Payment | UNIQUE reference, UNIQUE idempotency_key | Dedup |
| Payment | INDEX (status, created_at) | Status queries |
| Payment | INDEX gateway_reference | Webhook lookup |
| WebhookEvent | UNIQUE (gateway, event_id) | Idempotent webhooks |
| AuditLog | INDEX (event_type, created_at), (user, created_at) | Security queries |
| User | UNIQUE email | Login |

### Missing / recommended

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| Payment(user_id, created_at) | MEDIUM | Portal payment list pagination |
| Invoice(user_id, status) | LOW | Dashboard open invoice count |
| Subscription(user_id, status) | LOW | Active subscription lookups |
| AuditLog immutability | MEDIUM | DB trigger or separate audit store |
| Financial ledger tables | CRITICAL (roadmap) | Not present — required for MFI core |

---

## Migration hygiene

| Check | Status | Evidence |
|-------|--------|----------|
| CI migration drift check | ✅ | `.github/workflows/ci.yml:47` |
| Squashed migrations | ❌ | Per-app linear migrations |
| Data migrations for nav/sync | ✅ | control_room migrations 0003–0011 |

---

## PostgreSQL configuration

```python
# config/settings/base.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "CONN_MAX_AGE": 600,
        "OPTIONS": {"connect_timeout": 10},
    }
}
```

| Setting | Assessment |
|---------|------------|
| CONN_MAX_AGE=600 | Good for Gunicorn workers; watch connection limits |
| No statement_timeout | MEDIUM — long queries can block workers |
| No SSL mode in OPTIONS | MEDIUM — should enforce `sslmode=require` in prod |
| Single database | Expected for current scale |

---

## Data integrity risks

| Risk | Severity | Detail |
|------|----------|--------|
| No FK from Payment to Subscription | LOW | Linked via invoice/plan only |
| SET_NULL on invoice when payment deleted path unclear | LOW | CASCADE on user deletes payments |
| JSON metadata fields unvalidated | LOW | Payment.metadata, AuditLog.metadata |
| Decimal(12,2) for money | ✅ | Adequate for subscription amounts |
| No currency exchange table | N/A | Multi-currency display only |

---

## UUID usage

All `BaseModel` entities use UUID v4 primary keys (`core/models/__init__.py`). Benefits:
- Non-enumerable IDs in URLs
- Safer public exposure of object references

---

## Backup and recovery

| Item | Status |
|------|--------|
| Automated backup scripts in repo | ❌ Not found |
| Documented backup procedure | ⚠️ Partial in deployment docs |
| Point-in-time recovery | ❌ Not configured in repo |

**Recommendation:** Document and automate `pg_dump` + media backup before enterprise upgrade.

---

## Test database parity

Tests use SQLite in-memory (`config/settings/test.py`). Implications:
- PostgreSQL-specific features not tested
- Constraint behavior may differ
- Recommend CI job with PostgreSQL for integration tests (CI already uses Postgres for test run ✅)

---

## Financial schema gap

**No tables exist for:**
- Chart of accounts
- Journal entries / ledger lines
- Loan accounts, schedules, disbursements
- Savings accounts, deposits, withdrawals
- Interest accrual, penalties, fees
- Business date / period close

See `ZRETA_FINANCIAL_AUDIT.md`.
