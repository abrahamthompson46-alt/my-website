# Platform sanitization

**Last updated:** 2026-09-14

## Goal

Keep **database state and UI expectations** aligned for the Zreta storefront + billing platform (not CoreTrust banking logic).

## Command

```bash
python manage.py sanitize_platform
python manage.py sanitize_platform --fix
```

Default is **dry-run** (report only). `--fix` applies safe repairs only.

### Safe repairs (`--fix`)

| Check | Action |
|-------|--------|
| `null_organization` | Backfill org from linked subscription/invoice or user default org |
| `license_org_mismatch` | Align license org to subscription org |
| `featured_policy` | Clear `is_featured` unless published GA/Beta |
| `coretrust_catalog` | Normalize CoreTrust name/status/external URL |
| `overdue_trials` | Expire overdue trials + active licenses |

### Report-only

| Check | Meaning |
|-------|---------|
| `cross_user_link` | Invoice/license user ≠ subscription user |
| `status_date_invariant` | Impossible status/date combinations |
| `stale_microfinance_copy` | Published CMS/docs still say “Microfinance Core” |

## Related

- Product model: `docs/ZRETA_PRODUCT_MODEL.md`
- Homepage sync: `python manage.py sync_homepage --products`
- Trial expiry cron: `python manage.py expire_trials`
