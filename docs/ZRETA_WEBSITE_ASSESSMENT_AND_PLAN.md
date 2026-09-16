# Zreta Website — Assessment & Implementation Plan

**Created:** 2026-09-16  
**Status:** Approved direction for incremental enterprise redesign (not a rebuild)  
**Sources:** External assessment report + Cursor codebase/production review after storefront honesty deploy (`0ed6542`)

---

## 1. Executive verdict

The assessment is **largely correct** and aligns with what the codebase and live site show.

| Dimension | Verdict |
|-----------|---------|
| Product / platform concept | Strong — keep |
| Storefront architecture (products + billing) | Strong — already real |
| Navigation structure | Good foundation; too crowded |
| Credibility / customer proof | **Primary gap** |
| Consistency (naming, trial, currency) | Partially fixed in code; CMS/ops still need vigilance |
| Depth (product pages, security, support) | Needs Phase 2–3 content work |
| Conversion | Needs homepage + industry landing work |
| Visual rebuild | **Do not** prioritize animation/gradients |

**Single rule:** replace “what we say” with “what we can prove.” Prefer evidence, screenshots, architecture, and honest Live / Roadmap labels over broader claims.

---

## 2. What Zreta already does well (confirmed)

1. **Clear platform model** — Zreta markets/bills modular products; ChurchHub and CoreTrust are external live apps (`docs/ZRETA_PRODUCT_MODEL.md`).
2. **Honest live vs roadmap catalog** — after migrate `0006` + `sync_homepage --products`, featured/homepage intent products are limited to ChurchHub + CoreTrust.
3. **Buyer path exists** — Home → product → pricing/demo/trial → portal billing/launch.
4. **Enterprise scaffolding** — docs portal, status page, security pages seeds, portal, payments, MFA/audit in platform.
5. **Africa/Ghana positioning hooks** — GHS, Mobile Money, regional gateways already in trust copy (need concrete depth, not slogans).

---

## 3. Cursor additions to the assessment

These points extend the external report with repo/production specifics:

### A. Production lag is part of the credibility problem
Even after code fixes, stale CMS can reintroduce “14 days”, “Microfinance Core”, or over-broad featured products until operators run:

```bash
python manage.py sync_homepage --products
python manage.py sanitize_platform --fix
```

**Plan implication:** every content release includes a sync/sanitize checklist (already in `docs/ZRETA_DEPLOYMENT_PROCEDURE.md`).

### B. Dual acquisition paths must stay explicit
- **ChurchHub:** external apply/contact (`mychurch.zreta.com`)
- **CoreTrust:** external request-demo (`micro.zreta.com/request-demo/`)
- **Zreta portal:** billing, invoices, launch links after purchase

Do not market “instant self-serve trial on every product” for CoreTrust or roadmap SKUs.

### C. CoreTrust brand drift is not only on Zreta.com
The linked product site still brands as “CTF System” in places. Website honesty alone cannot fix that; CoreTrust product branding is a **cross-repo** workstream.

### D. Empty Case Studies / Success Stories links actively hurt
Prefer hide/rename until one real story exists — honesty without a commercial wound.

### E. Security Center is high leverage *because engineering already exists*
MFA, audit logs, private payment proofs, CSRF, status/health, published security pages. Marketing should surface existing controls, not invent new claims.

### F. Do not expand purchasable GA catalog without outbound URLs
`products/services/live_products.py` allowlists live storefront slugs for homepage feature/intent. Keep that gate; accidental GA on ERP must not re-enter homepage CTAs.

---

## 4. Recommended site information architecture

```
ZRETA — Enterprise software platform
│
├── Home
├── Products
│   ├── ChurchHub (Live)
│   ├── CoreTrust (Live)
│   ├── ERP (Roadmap / Early Access when true)
│   ├── School / Hospital / HR (Coming soon)
│   └── Compare
├── Solutions (industry landings)
│   ├── Churches
│   ├── Microfinance
│   ├── Enterprises
│   ├── Education
│   └── Healthcare
├── Platform
│   ├── Architecture
│   ├── Security Center
│   ├── Payments & billing
│   ├── Integrations / API
│   └── Infrastructure & status
├── Customers (only when content exists)
│   ├── Stories
│   └── Logos / proof
├── Resources
│   ├── Blog / Guides
│   ├── Docs
│   ├── White papers
│   └── Videos
├── Pricing
├── Company (About, Contact, Careers, Partners)
└── Support (Help, Tickets, Status, SLAs)
```

**Primary nav (target):** `Products | Solutions | Platform | Resources | Pricing`  
**Right cluster:** `Login | Request demo | Start trial`

---

## 5. Implementation plan (phased)

Work is incremental. Each phase ships independently. Prefer content + CMS sync over redesign fireworks.

### Phase 1 — Credibility & consistency (P0)

**Goal:** No unsupported claims; no contradictory numbers; clear Live vs Roadmap.

| ID | Work item | Owner area | Acceptance |
|----|-----------|------------|------------|
| P1-01 | Standardize trial to **30 days** everywhere (templates, CMS, hero trust, FAQs, pricing cards) | website/cms | Grep finds no “14-day” on public pages |
| P1-02 | Currency clarity: show **GHS** (or USD) explicitly on pricing cards; remove mixed “₵ + USD footnote” confusion | products templates | Pricing page states currency next to amount |
| P1-03 | CoreTrust naming: public UI says **CoreTrust** only; legacy “Microfinance Core” only in historical docs if needed | sanitize + CMS | `sanitize_platform` dry-run shows 0 stale hits |
| P1-04 | Soften/remove unproven trust lines (“global organizations trust”) until proof exists | content/CMS | Homepage trust claim is evidence-based or removed |
| P1-05 | Hide or rename empty Case Studies / Success Stories until first real story | nav + marketing | No “No case studies yet” dead-end in primary nav |
| P1-06 | About/Company page with real company facts (location, what Zreta sells, what is external) | website/pages | About answers “is this a real company?” |
| P1-07 | Security Center v1: index page linking existing security/privacy/status docs + MFA/RBAC/audit bullets that are true | website | `/security/` (or `/platform/security/`) is a coherent hub |
| P1-08 | Support Center v1: help entry, ticket path, docs, status, contact | support templates | Support page is not an empty shell |
| P1-09 | Live / Early Access / Coming soon badges consistent on cards, detail, nav | products | ERP not presented as equally mature as ChurchHub |
| P1-10 | Post-deploy content gate: sync_homepage + sanitize in every release | ops docs | Checklist item checked on VPS |

**Exit criteria:** Fresh visitor cannot find a 14/30 conflict, CoreTrust rename flake, empty case-study trap, or “trusted globally” without proof.

### Phase 2 — Conversion (P1)

**Goal:** Clearer homepage + stronger path to demo/trial for live products.

| ID | Work item | Acceptance |
|----|-----------|------------|
| P2-01 | Homepage hero rewrite: brand → one outcome sentence → Products / Demo CTAs; remove clutter from first viewport | Brand-first hero passes existing design rules |
| P2-02 | Product cards: Live vs Roadmap, one outcome line, one primary CTA | Cards scannable in <5s |
| P2-03 | Screenshot galleries for ChurchHub (and CoreTrust when allowed) | ≥3 real UI shots per live product |
| P2-04 | Short demo videos (or Loom embeds) on live product pages | One video per live product |
| P2-05 | CTA consistency: trial → product chooser / outbound; demo → request-demo | Matches outbound_links service |
| P2-06 | Industry landing pages: `/solutions/churches/`, `/solutions/microfinance/`, etc. | Outcome-led copy, not module lists only |
| P2-07 | Pricing page polish: monthly/annual, inclusions, support tier, currency | No ambiguous currency |
| P2-08 | Slim primary navigation to recommended IA | ≤5 primary items + auth/CTA cluster |

**Exit criteria:** Demo/trial conversion path is obvious on mobile and desktop for ChurchHub and CoreTrust.

### Phase 3 — Authority (P1/P2)

**Goal:** Prove expertise and depth.

| ID | Work item | Acceptance |
|----|-----------|------------|
| P3-01 | First real customer story (or keep Customers section hidden) | One verified story with measurable results |
| P3-02 | Testimonials only when verified (keep placeholders off homepage) | Existing honesty filters remain |
| P3-03 | Platform architecture page with diagram (Zreta shared services → products) | Public architecture page live |
| P3-04 | Security Center v2: auth, encryption, backups, disclosure | Linked from footer + platform nav |
| P3-05 | API/docs depth: examples, webhooks, permissions | Docs not shell-only |
| P3-06 | Industry guides on blog (loan arrears, church accountability, etc.) | ≥6 evergreen guides |
| P3-07 | Product page depth templates (esp. CoreTrust loan/finance/compliance sections) | Spec sections present; mark EXTERNAL vs platform |

**Exit criteria:** A skeptical MFI or church admin can evaluate fit from public pages without a sales call.

### Phase 4 — Enterprise positioning (P2)

**Goal:** Enterprise buying committee materials.

| ID | Work item | Acceptance |
|----|-----------|------------|
| P4-01 | Onboarding / migration offering page | Clear packages |
| P4-02 | SLA documentation (support tiers) | Published, not overclaimed |
| P4-03 | Privacy / data protection center | Linked from legal + security |
| P4-04 | Business continuity / DR summary (point to backup docs without overclaiming) | Accurate to `ZRETA_BACKUP_*` |
| P4-05 | Integration directory + partner program stubs | Only list real integrations |
| P4-06 | Enterprise contact / demo qualification workflow | CRM/ticket handoff works |
| P4-07 | Status page detail: component list + history when telemetry exists | No fake uptime charts |

**Exit criteria:** Procurement can find security, SLA, privacy, and support answers without email tennis.

---

## 6. Priority matrix (do first)

| Priority | Theme | Why |
|----------|--------|-----|
| **P0** | Credibility & consistency | Trust-sensitive verticals; empty proof pages and contradictions kill deals |
| **P0** | Live vs roadmap clarity | Stops overselling unfinished products |
| **P1** | Conversion (hero, CTAs, industry pages, screenshots) | Turns traffic into demos |
| **P1** | Security Center surfacing existing controls | Differentiator already paid for in engineering |
| **P2** | Authority content (stories, guides, API depth) | SEO + sales enablement |
| **P2** | Enterprise packet (SLA, privacy, DR) | Shortens enterprise sales cycle |
| **Defer** | Fancy motion, 3D, extra empty pages, fake logos | Actively harmful |

---

## 7. Explicit non-goals

- Full visual redesign / animation-first homepage
- Claiming SOC 2, global customer counts, or uptime % without evidence
- Building in-repo MFI/ERP engines inside this marketing monolith
- Publishing Case Studies with invented customers
- Treating CoreTrust product-site branding as fixed solely from this repo

---

## 8. Suggested first sprint (2 weeks)

1. P1-01…P1-05, P1-09 (consistency + empty-page removal)  
2. P1-06 About facts + P1-07 Security Center v1 shell  
3. P1-08 Support Center v1  
4. P2-01 hero rewrite using existing design system (no gradient spree)  
5. Capture ChurchHub screenshot set for P2-03  

---

## 9. Tracking

- Progress tracker: extend `docs/ZRETA_UPGRADE_PROGRESS.md` with a **Website credibility** section mirroring Phase IDs above.  
- Scope truth: keep `docs/ZRETA_SCOPE_TRUTH.md` as the legal/marketing claim gate.  
- Deploy: every marketing release runs sync + sanitize per `docs/ZRETA_DEPLOYMENT_PROCEDURE.md`.

---

## 10. Assessment scorecard (combined)

| Area | External view | Cursor view (post-0ed6542) |
|------|---------------|----------------------------|
| Brand concept | Strong | Agree |
| Product architecture | Strong | Agree — storefront + external apps |
| Navigation | Crowded | Agree — Phase 2 slim |
| Product presentation | Needs depth | Agree |
| Credibility | Major gap | Agree — **Phase 1** |
| Customer proof | Major gap | Agree — hide until real |
| Pricing clarity | Needs fix | Partially improved; finish currency/trial audit |
| Security positioning | Opportunity | Agree — surface existing engineering |
| Documentation | Good foundation | Agree — deepen |
| Support | Needs work | Agree |
| SEO potential | Strong | Agree — industry landings + guides |
| Africa positioning | Opportunity | Agree — make concrete |
| Conversion | Needs work | Agree — Phase 2 |
| Overall | Promising; needs proof | **Incremental redesign, not rebuild** |
