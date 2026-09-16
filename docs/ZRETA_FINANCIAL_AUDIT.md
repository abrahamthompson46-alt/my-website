# Zreta Platform — Financial System Audit

**Audit date:** 2026-08-13  
**Scope:** All financial functionality in repository as-is

---

## Executive verdict

**This repository does NOT contain a core banking or accounting system.** Financial functionality is limited to **SaaS subscription billing and payment collection**. Loans, savings, ledger, double-entry accounting, interest, penalties, period close, and reconciliation (in the banking sense) are **not implemented** — they appear only in marketing seed data for the "Microfinance Core" product page.

---

## What IS implemented

### Payment collection (`payments` app)

| Capability | Status | Location |
|------------|--------|----------|
| One-time checkout | ✅ | `payments/services/checkout.py` |
| Gateway adapters (Paystack, Flutterwave, Hubtel) | ✅ | `payments/gateways/` |
| Manual payment methods (bank transfer, cash, cheque) | ✅ | `ManualPaymentDetail` |
| Webhook processing | ✅ | `payments/services/webhooks.py` |
| Refunds (model + service) | ✅ | `payments/models/refund.py`, `services/refunds.py` |
| Recurring payment records | ✅ | `payments/models/recurring.py` |
| Gateway reconciliation records | ✅ | `payments/models/reconciliation.py` |
| Invoice linkage | ✅ | Payment.invoice FK |
| Idempotency key on Payment | ✅ | Unique constraint |
| Webhook idempotency | ✅ | WebhookEvent unique (gateway, event_id) |

### Customer billing (`customer_portal` app)

| Capability | Status |
|------------|--------|
| Subscriptions | ✅ |
| Invoices (open/paid/overdue) | ✅ |
| Licenses | ✅ |
| Trial provisioning | ✅ (`common/services/trial_provisioning.py`) |

### Money handling

| Capability | Status | Location |
|------------|--------|----------|
| Decimal storage | ✅ | DecimalField(12,2) |
| Quantization helpers | ✅ | `common/money.py` |
| Cedi display formatting | ✅ | `common/templatetags/common_tags.py` |
| Minor unit normalization in webhooks | ✅ | `_MINOR_UNIT_GATEWAYS` in webhooks.py |

---

## What is NOT implemented

| Domain | Evidence of absence |
|--------|---------------------|
| Chart of accounts | No models |
| Journal entries | No models |
| Double-entry bookkeeping | No debit/credit logic |
| General ledger | No models |
| Loan origination/disbursement | Seed copy only |
| Loan schedules/repayments | No models |
| Savings accounts | No models |
| Interest calculation/accrual | No services |
| Penalties/fees (banking) | No models |
| Reversals (accounting) | Payment refund only |
| Approval workflows (financial) | Manual payment confirmation field only |
| Business date / EOD | No models |
| Period closing | No models |
| Bank reconciliation (ledger) | Gateway reconciliation only |
| Concurrent posting controls | Partial (DB transactions on webhook) |
| Audit trail for financial postings | Auth audit only, not financial |

---

## Payment flow analysis

```
Customer → CheckoutView → create_checkout() [@transaction.atomic]
         → Gateway API → authorization_url
         → Provider webhook → process_webhook() [@transaction.atomic]
         → sync_payment_success() → invoice/subscription update
```

### FIN-001 — Client-supplied checkout amount

| Field | Value |
|-------|-------|
| **Severity** | CRITICAL (for billing integrity) |
| **Location** | `payments/views.py:145-154` |
| **What** | User can POST arbitrary `amount` when no invoice/plan |
| **Impact** | Underpayment for subscriptions; revenue loss |
| **Evidence** | Direct Decimal conversion from POST |
| **Fix** | Server-side price from PricingTier only |
| **Complexity** | Low |

### FIN-002 — Webhook amount validation (good)

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL (strength) |
| **Location** | `payments/services/webhooks.py:87-103` |
| **What** | Validates currency, amount (with minor unit normalization), gateway reference |
| **Impact** | Prevents provider mismatch attacks |
| **Tests** | `payments/tests/test_webhook_validation.py` (4 tests) |

### FIN-003 — Terminal state protection (good)

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL (strength) |
| **Location** | `webhooks.py:88-89` |
| **What** | Rejects webhooks for already-succeeded payments |
| **Impact** | Reduces duplicate posting |

### FIN-004 — No double-entry on payment success

| Field | Value |
|-------|-------|
| **Severity** | HIGH (for fintech roadmap) |
| **Location** | `payments/services/billing_sync.py` |
| **What** | Payment success updates invoice status; no ledger entries |
| **Impact** | Cannot produce financial statements, trial balance, regulatory reports |
| **Fix** | Implement ledger module before MFI launch |
| **Complexity** | Very High (months) |

### FIN-005 — Race condition on concurrent webhooks

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Location** | `webhooks.py:31-42, 106-120` |
| **What** | `get_or_create` on WebhookEvent prevents duplicate event processing; payment status update not using `select_for_update` |
| **Impact** | Theoretical double sync under concurrent identical events; mitigated by terminal state check |
| **Fix** | `select_for_update()` on Payment row in webhook handler |
| **Complexity** | Low |

### FIN-006 — Manual payment confirmation

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Location** | `ManualPaymentDetail.confirmed_by` |
| **What** | Staff confirmation tracked but no workflow engine |
| **Impact** | Unauthorized confirmation possible if staff RBAC insufficient on confirm action |
| **Fix** | Audit confirm action; permission gate; dual control for enterprise |
| **Complexity** | Medium |

### FIN-007 — Currency hardcoded fallback USD

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Location** | `payments/views.py:119, 154` |
| **What** | Default currency USD when not from tier |
| **Impact** | GHS products may checkout in wrong currency if tier missing |
| **Fix** | Default to platform setting or product currency |
| **Complexity** | Trivial |

### FIN-008 — Refund logic exists but limited tests

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Location** | `payments/services/refunds.py` |
| **What** | Refund service present; no dedicated test file found |
| **Impact** | Refund bugs could cause balance discrepancies |
| **Fix** | Add refund integration tests |
| **Complexity** | Low |

---

## Double-entry assessment

**Not applicable to current codebase.** Payment records are single-sided transaction logs, not accounting entries.

For future MFI core, minimum requirements:
- Immutable journal with debit/credit pairs
- Account types (asset, liability, equity, income, expense)
- Posting rules engine
- Business date vs system date
- Reversal entries (not deletes)
- Period lock after close

---

## Concurrency assessment

| Operation | Transaction boundary | Row locking |
|-----------|---------------------|-------------|
| create_checkout | `@transaction.atomic` | None |
| process_webhook | `@transaction.atomic` | None |
| verify_payment | `@transaction.atomic` | None |
| sync_payment_success | Called inside atomic | Unknown without reading billing_sync |

**Recommendation:** Add `select_for_update()` on Payment and Invoice during status transitions.

---

## Audit trail (financial)

Current `AuditLog` covers authentication and product/demo events — **not payment postings**.

| Event | Logged? |
|-------|---------|
| Payment created | ❌ |
| Payment succeeded | ❌ |
| Webhook received | ❌ (WebhookEvent model only) |
| Refund issued | ❌ |
| Manual payment confirmed | ❌ |
| Invoice status change | ❌ |

**Recommendation:** Add `AuditEventType.PAYMENT_*` events before enterprise launch.

---

## Critical financial risks (current system)

1. **Checkout amount manipulation** — revenue integrity
2. **No ledger** — cannot build MFI product on this codebase without greenfield financial module
3. **Missing payment audit events** — compliance gap
4. **Public payment proof storage** — PII/financial document exposure

---

## Critical financial risks (future MFI build)

1. Interest calculation errors without property-based tests
2. Race conditions on concurrent loan repayments
3. Missing idempotency on disbursement API
4. No business date — backdating attacks
5. Period close bypass

These are **forward-looking** — none apply today because loan/savings code does not exist.
