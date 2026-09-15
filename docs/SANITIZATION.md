# Platform sanitization

**Last updated:** 2026-09-15

## Goal

Keep **database state and UI expectations** aligned for the Zreta storefront + billing platform (not CoreTrust banking logic).

## Command

```bash
python manage.py sanitize_platform
python manage.py sanitize_platform --fix
```

Default is **dry-run** (report only). `--fix` applies safe repairs.

### Safe repairs (`--fix`)

| Check | Action |
|-------|--------|
| `null_organization` | Backfill org from linked subscription/invoice or user default org |
| `license_org_mismatch` | Align license org to subscription org |
| `cross_user_link` | Detach bad invoice subscription links; revoke mismatched licenses |
| `status_date_invariant` | Fill missing paid/cancel/trial dates; expire licenses on expired subs |
| `featured_policy` | Clear `is_featured` unless published GA/Beta |
| `coretrust_catalog` | Normalize CoreTrust name/status/external URL |
| `stale_microfinance_copy` | Rewrite “Microfinance Core” → “CoreTrust” in CMS/docs/marketing |
| `overdue_trials` | Expire overdue trials + active licenses |

## UI consistency

- Trial/buy CTAs only show for **published GA/Beta** products (`is_purchasable`)
- Coming soon / draft / deprecated products show learn-more / live-app / demo instead
- Plan start + checkout reject non-purchasable products

## Related

- Product model: `docs/ZRETA_PRODUCT_MODEL.md`
- Homepage sync: `python manage.py sync_homepage --products`
- Trial expiry cron: `python manage.py expire_trials`
