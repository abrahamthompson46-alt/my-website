# Zreta product model

**Last updated:** 2026-09-14

## What this repository is

**Zreta.com** (this repo) is the **marketing site + customer portal + billing platform** for Zreta products.

It is **not** the place where vertical product engines (ChurchHub, CoreTrust, etc.) are implemented.

## What products are

| Product | Role of this website | Where the product runs |
|---------|----------------------|-------------------------|
| **ChurchHub** | Catalog, pricing, portal billing, links | External app (`mychurch.zreta.com`) |
| **CoreTrust** (MFI) | Catalog, pricing, portal billing, links | External app (`micro.zreta.com`) — already built and live |
| Other catalog products | Marketing / roadmap entries | Separate apps when they exist |

Pattern for every live product:

1. Product page on Zreta (features, pricing, trial)
2. Customer portal subscription / invoice / license
3. `external_app_url` (and optional demo/register URLs) pointing at the real product
4. No duplicate domain engine inside this monolith

## What we do **not** build here

- Chart of accounts / general ledger for MFIs  
- Business-date / EOD banking calendars  
- Borrower registries for lending  
- Loan origination, disbursement, repayments, savings interest  

Those belong in **CoreTrust** (or whichever product owns that domain).

## Historical note

In September 2026, Phase 3 briefly added in-repo `ledger` and `clients` apps under the assumption that Microfinance Core would be built inside this monolith. That was the wrong product model. Those apps were removed; CoreTrust remains the live MFI product.
