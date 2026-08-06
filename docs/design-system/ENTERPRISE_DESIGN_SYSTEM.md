# Enterprise Design System
## Unified Visual Language for Multi-Product SaaS Platform

**Version:** 1.0.0  
**Status:** Approved  
**Scope:** Public marketing site, customer portal, partner portal, admin console  
**Philosophy:** Clarity, trust, density-with-breathing-room — aligned with Microsoft Fluent, Stripe, Salesforce Lightning, and Oracle Redwood principles

---

## 1. Design Principles

| Principle | Definition | Application |
|-----------|------------|-------------|
| **Clarity over decoration** | Every element serves comprehension or action | No ornamental UI; whitespace is structural |
| **Trust by default** | Visual language signals enterprise reliability | Consistent blues, neutral surfaces, predictable patterns |
| **Scalable density** | Information-rich without clutter | Tighter spacing in dashboards; generous spacing in marketing |
| **Accessible first** | WCAG 2.1 AA minimum; AAA where feasible | Color contrast, focus, motion, screen reader support |
| **Product-neutral shell** | Portal chrome is neutral; product accent is contextual | Brand color applied sparingly per product context |
| **Responsive parity** | Mobile is not a degraded experience | Touch targets, collapsible nav, stacked layouts |
| **Mode coherence** | Light and dark are first-class, not inverted afterthoughts | Semantic tokens, not hardcoded colors |

---

## 2. Brand Architecture

### 2.1 Color Hierarchy

The platform uses a **company master brand** (primary blue) with **product accent tokens** applied only in product-specific contexts.

```
Company Master Brand
├── Primary (Blue)      → CTAs, links, active states, key actions
├── Secondary (Slate)   → Text, borders, surfaces
├── Semantic            → Success, warning, error, info
└── Product Accents     → ChurchHub, Microfinance, ERP, School, Hospital, HR
```

### 2.2 Product Accent Colors (Contextual Only)

| Product | Token | Hex | Usage |
|---------|-------|-----|-------|
| ChurchHub | `--product-churchhub` | `#6366F1` | Product badge, hero accent, portal product card |
| Microfinance Core | `--product-microfinance` | `#0D9488` | Same pattern |
| ERP Suite | `--product-erp` | `#2563EB` | Same pattern |
| School Management | `--product-school` | `#7C3AED` | Same pattern |
| Hospital Management | `--product-hospital` | `#0891B2` | Same pattern |
| HR & Payroll | `--product-hr` | `#EA580C` | Same pattern |
| Future products | `--product-future-N` | TBD from palette slot | Extensible slot system |

Product accents **never replace** the master primary for global navigation or primary CTAs.

---

## 3. Color Palette

### 3.1 Primary — Enterprise Blue

Inspired by Stripe/Salesforce trust palette. Blue communicates reliability and action.

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `--color-primary-50` | `#EFF6FF` | `#0C1929` | Subtle backgrounds |
| `--color-primary-100` | `#DBEAFE` | `#102A4C` | Hover backgrounds |
| `--color-primary-200` | `#BFDBFE` | `#1E3A5F` | Borders, dividers (accent) |
| `--color-primary-300` | `#93C5FD` | `#2563EB33` | Disabled accents |
| `--color-primary-400` | `#60A5FA` | `#3B82F6` | Icons, secondary links |
| `--color-primary-500` | `#3B82F6` | `#60A5FA` | **Default primary** |
| `--color-primary-600` | `#2563EB` | `#3B82F6` | **Primary buttons, links** |
| `--color-primary-700` | `#1D4ED8` | `#2563EB` | Hover primary |
| `--color-primary-800` | `#1E40AF` | `#1D4ED8` | Active/pressed |
| `--color-primary-900` | `#1E3A8A` | `#1E40AF` | Dark accents |

### 3.2 Neutral — Slate Scale

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `--color-neutral-0` | `#FFFFFF` | `#0F172A` | Base background |
| `--color-neutral-50` | `#F8FAFC` | `#1E293B` | Subtle surface |
| `--color-neutral-100` | `#F1F5F9` | `#334155` | Card alt, table stripe |
| `--color-neutral-200` | `#E2E8F0` | `#475569` | Borders default |
| `--color-neutral-300` | `#CBD5E1` | `#64748B` | Borders strong |
| `--color-neutral-400` | `#94A3B8` | `#94A3B8` | Placeholder text |
| `--color-neutral-500` | `#64748B` | `#CBD5E1` | Secondary text |
| `--color-neutral-600` | `#475569` | `#E2E8F0` | Body text (dark mode) |
| `--color-neutral-700` | `#334155` | `#F1F5F9` | Headings (dark mode) |
| `--color-neutral-800` | `#1E293B` | `#F8FAFC` | Primary text (light mode) |
| `--color-neutral-900` | `#0F172A` | `#FFFFFF` | Headings (light mode) |

### 3.3 Semantic Colors

| Role | Light Background | Light Foreground | Dark Background | Dark Foreground |
|------|------------------|------------------|-----------------|-----------------|
| Success | `#ECFDF5` | `#047857` | `#064E3B` | `#6EE7B7` |
| Warning | `#FFFBEB` | `#B45309` | `#78350F` | `#FCD34D` |
| Error | `#FEF2F2` | `#B91C1C` | `#7F1D1D` | `#FCA5A5` |
| Info | `#EFF6FF` | `#1D4ED8` | `#1E3A8A` | `#93C5FD` |

Semantic tokens: `--color-success-*`, `--color-warning-*`, `--color-error-*`, `--color-info-*` (each: bg, fg, border, icon).

### 3.4 Surface & Elevation (Light Mode)

| Token | Value | Usage |
|-------|-------|-------|
| `--surface-page` | `neutral-0` | Page background |
| `--surface-section` | `neutral-50` | Alternating sections |
| `--surface-card` | `neutral-0` | Cards, modals |
| `--surface-raised` | `neutral-0` + shadow | Dropdowns, popovers |
| `--surface-overlay` | `#0F172A` @ 50% | Modal backdrop |
| `--surface-sidebar` | `neutral-50` | Portal sidebar |
| `--surface-header` | `neutral-0` | Sticky header |

### 3.5 Surface & Elevation (Dark Mode)

| Token | Value | Usage |
|-------|-------|-------|
| `--surface-page` | `#0B1120` | Deep page background |
| `--surface-section` | `#0F172A` | Section alternation |
| `--surface-card` | `#1E293B` | Cards |
| `--surface-raised` | `#334155` | Elevated elements |
| `--surface-overlay` | `#000000` @ 60% | Modal backdrop |
| `--surface-sidebar` | `#0F172A` | Portal sidebar |
| `--surface-header` | `#0F172A` | Sticky header |

### 3.6 Contrast Requirements

| Pairing | Minimum Ratio | Target |
|---------|---------------|--------|
| Body text on page | 4.5:1 | 7:1 for long-form |
| Large text (≥18px bold / 24px) | 3:1 | 4.5:1 |
| UI components & icons | 3:1 | 4.5:1 |
| Primary button text | 4.5:1 | Always white on primary-600+ |
| Focus ring | 3:1 against adjacent | 2px solid primary-500 |

---

## 4. Typography

### 4.1 Font Stack

| Role | Font Family | Fallback |
|------|-------------|----------|
| **Display & UI** | Inter | system-ui, -apple-system, Segoe UI, sans-serif |
| **Monospace** | JetBrains Mono | ui-monospace, Consolas, monospace |

Inter is loaded via variable font (woff2) with `font-display: swap`.

### 4.2 Type Scale

Base: **16px** (1rem). Scale ratio: **1.250 (Major Third)** with manual overrides for enterprise density.

| Token | Size | Line Height | Weight | Letter Spacing | Usage |
|-------|------|-------------|--------|----------------|-------|
| `--text-display-xl` | 3.75rem (60px) | 1.1 | 700 | -0.02em | Marketing hero (desktop) |
| `--text-display-lg` | 3rem (48px) | 1.15 | 700 | -0.02em | Page heroes |
| `--text-display-md` | 2.25rem (36px) | 1.2 | 700 | -0.015em | Section headers |
| `--text-heading-xl` | 1.875rem (30px) | 1.25 | 600 | -0.01em | H1 |
| `--text-heading-lg` | 1.5rem (24px) | 1.3 | 600 | -0.01em | H2 |
| `--text-heading-md` | 1.25rem (20px) | 1.4 | 600 | 0 | H3 |
| `--text-heading-sm` | 1.125rem (18px) | 1.4 | 600 | 0 | H4, card titles |
| `--text-body-lg` | 1.125rem (18px) | 1.6 | 400 | 0 | Lead paragraphs |
| `--text-body-md` | 1rem (16px) | 1.6 | 400 | 0 | Body default |
| `--text-body-sm` | 0.875rem (14px) | 1.5 | 400 | 0 | Secondary body, tables |
| `--text-caption` | 0.75rem (12px) | 1.4 | 400 | 0.01em | Labels, meta, badges |
| `--text-overline` | 0.6875rem (11px) | 1.3 | 600 | 0.08em | Section labels (uppercase) |

### 4.3 Font Weights

| Token | Value | Usage |
|-------|-------|-------|
| `--font-regular` | 400 | Body |
| `--font-medium` | 500 | Buttons, nav items, labels |
| `--font-semibold` | 600 | Headings, emphasis |
| `--font-bold` | 700 | Display, hero |

### 4.4 Typography Rules

- **Maximum line length:** 65–75 characters for marketing prose; 80 for dashboards
- **Paragraph spacing:** 1em bottom margin
- **Heading hierarchy:** Never skip levels (H1 → H2 → H3)
- **Links:** `--color-primary-600`, underline on hover only (marketing); always underlined in body copy for accessibility option B
- **Truncation:** Single-line ellipsis for table cells; max 2 lines with line-clamp for card descriptions
- **Numbers & data:** Tabular figures (`font-variant-numeric: tabular-nums`) in tables, dashboards, pricing

---

## 5. Spacing & Layout

### 5.1 Spacing Scale (4px base)

| Token | Value |
|-------|-------|
| `--space-0` | 0 |
| `--space-1` | 0.25rem (4px) |
| `--space-2` | 0.5rem (8px) |
| `--space-3` | 0.75rem (12px) |
| `--space-4` | 1rem (16px) |
| `--space-5` | 1.25rem (20px) |
| `--space-6` | 1.5rem (24px) |
| `--space-8` | 2rem (32px) |
| `--space-10` | 2.5rem (40px) |
| `--space-12` | 3rem (48px) |
| `--space-16` | 4rem (64px) |
| `--space-20` | 5rem (80px) |
| `--space-24` | 6rem (96px) |

### 5.2 Layout Grid

| Context | Max Width | Columns | Gutter | Margin |
|---------|-----------|---------|--------|--------|
| Marketing | 1280px | 12 | 24px | 24px (mobile: 16px) |
| Marketing wide | 1440px | 12 | 32px | 32px |
| Portal/Dashboard | Fluid | 12 | 24px | 24px |
| Admin console | Fluid | 12 | 16px | 16px |
| Content prose | 720px | — | — | centered |

### 5.3 Breakpoints

| Token | Min Width | Target |
|-------|-----------|--------|
| `--bp-xs` | 0 | Mobile portrait |
| `--bp-sm` | 640px | Mobile landscape |
| `--bp-md` | 768px | Tablet |
| `--bp-lg` | 1024px | Desktop |
| `--bp-xl` | 1280px | Large desktop |
| `--bp-2xl` | 1536px | Wide screens |

**Mobile-first:** Base styles target xs; enhancements at sm/md/lg/xl.

### 5.4 Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-none` | 0 | Tables, full-bleed |
| `--radius-sm` | 4px | Badges, tags, inputs |
| `--radius-md` | 6px | Buttons, cards (default) |
| `--radius-lg` | 8px | Modals, large cards |
| `--radius-xl` | 12px | Marketing cards, hero panels |
| `--radius-2xl` | 16px | Feature blocks |
| `--radius-full` | 9999px | Avatars, pills |

### 5.5 Shadows

| Token | Light Mode | Usage |
|-------|------------|-------|
| `--shadow-xs` | `0 1px 2px rgba(15,23,42,0.05)` | Subtle lift |
| `--shadow-sm` | `0 1px 3px rgba(15,23,42,0.08), 0 1px 2px rgba(15,23,42,0.04)` | Cards |
| `--shadow-md` | `0 4px 6px -1px rgba(15,23,42,0.08), 0 2px 4px -2px rgba(15,23,42,0.04)` | Dropdowns |
| `--shadow-lg` | `0 10px 15px -3px rgba(15,23,42,0.08), 0 4px 6px -4px rgba(15,23,42,0.04)` | Modals |
| `--shadow-xl` | `0 20px 25px -5px rgba(15,23,42,0.08), 0 8px 10px -6px rgba(15,23,42,0.04)` | Marketing elevation |

Dark mode shadows use higher opacity black: `rgba(0,0,0,0.3–0.5)`.

---

## 6. Buttons

### 6.1 Button Hierarchy

| Variant | Purpose | Background | Text | Border |
|---------|---------|------------|------|--------|
| **Primary** | Main action (1 per view) | `primary-600` | white | none |
| **Secondary** | Alternative action | transparent | `primary-600` | `primary-600` |
| **Tertiary / Ghost** | Low emphasis | transparent | `neutral-700` | none |
| **Destructive** | Delete, cancel subscription | `error-fg` | white | none |
| **Destructive outline** | Secondary destructive | transparent | `error-fg` | `error-fg` |
| **Link** | Inline navigation | transparent | `primary-600` | none, underline on hover |

### 6.2 Button Sizes

| Size | Height | Padding X | Font Size | Icon Size | Min Width |
|------|--------|-----------|-----------|-----------|-----------|
| **xs** | 28px | 10px | 12px | 14px | — |
| **sm** | 32px | 12px | 14px | 16px | — |
| **md** (default) | 40px | 16px | 14px | 18px | 80px (primary CTAs) |
| **lg** | 48px | 20px | 16px | 20px | 120px (hero CTAs) |
| **xl** | 56px | 24px | 16px | 22px | 140px (marketing hero) |

### 6.3 Button States

| State | Visual Change |
|-------|---------------|
| Default | Base variant styles |
| Hover | Background −1 shade; shadow-sm on primary |
| Active/Pressed | Background −2 shade; shadow-none; scale(0.98) |
| Focus | 2px focus ring offset 2px (`--color-primary-500`) |
| Disabled | Opacity 0.5; pointer-events none; no hover |
| Loading | Spinner replaces leading icon; text optional; width locked |

### 6.4 Button Composition

- **Icon + label:** Icon leading (16–20px), 8px gap
- **Icon only:** Square button, requires `aria-label`
- **Button group:** 8px gap; secondary left, primary right (Western LTR)
- **Split button:** Primary action + chevron dropdown (admin contexts)

### 6.5 Context Rules

- Marketing hero: max 2 buttons (primary + secondary)
- Modals: primary right-aligned in footer
- Destructive confirmations: destructive outline + primary cancel (safe action is primary)
- Tables: sm size, ghost variant for row actions

---

## 7. Forms

### 7.1 Input Types Covered

Text, email, password, number, tel, url, search, textarea, select, multi-select, checkbox, radio, switch/toggle, date picker, file upload, combobox/autocomplete.

### 7.2 Input Anatomy

```
[Label *]                    [Optional hint link]
[Prefix icon | Input field                    | Suffix icon]
[Helper text                                    ]
[Error message                                  ]
```

### 7.3 Input Sizing

| Size | Height | Padding | Font |
|------|--------|---------|------|
| sm | 32px | 8px 12px | 14px |
| md | 40px | 10px 14px | 14px |
| lg | 48px | 12px 16px | 16px |

### 7.4 Input States

| State | Border | Background | Label |
|-------|--------|------------|-------|
| Default | `neutral-200` | `surface-card` | `neutral-700` |
| Hover | `neutral-300` | unchanged | unchanged |
| Focus | `primary-500` 2px ring | unchanged | `primary-600` |
| Error | `error-fg` | `error-bg` subtle | `error-fg` |
| Disabled | `neutral-200` | `neutral-50` | `neutral-400` |
| Read-only | `neutral-200` | `neutral-50` | unchanged |

### 7.5 Label & Helper Text

- Labels: `--text-body-sm`, `--font-medium`, above input, 4px gap
- Required indicator: red asterisk + `aria-required="true"`
- Optional label suffix: "(optional)" in `--text-caption`, `neutral-500`
- Helper text: `--text-caption`, `neutral-500`, 4px below input
- Error text: `--text-caption`, `error-fg`, with error icon; `aria-describedby` linked

### 7.6 Checkbox & Radio

- Size: 18px × 18px (checkbox), 18px diameter (radio)
- Border: 2px `neutral-300`; checked: fill `primary-600`
- Focus: 2px focus ring
- Label: 8px gap, clickable (label wraps control)
- Group spacing: 12px vertical between options

### 7.7 Switch/Toggle

- Track: 44px × 24px; thumb: 20px
- Off: `neutral-200`; On: `primary-600`
- Focus ring on track
- Label left or right (consistent per form)

### 7.8 Select & Combobox

- Chevron trailing icon
- Dropdown panel: `--shadow-lg`, `--radius-md`, max-height 240px scroll
- Selected item: `primary-50` bg (light) / `primary-900` (dark)
- Keyboard: arrow nav, Enter select, Escape close

### 7.9 Form Layout Patterns

| Pattern | Usage |
|---------|-------|
| Single column | Mobile, simple forms |
| Two column | Desktop settings (label left 30%, input right 70%) |
| Field groups | Related fields in bordered section with group legend |
| Inline | Search bars, filters (label visually hidden) |
| Stepped/wizard | Progress indicator top; one section per step |

### 7.10 Validation UX

- Inline validation on blur (not on every keystroke except password strength)
- Form-level error summary at top for submit failures (linked to fields)
- Success state: green check icon inline (optional, sparingly)

---

## 8. Cards

### 8.1 Card Variants

| Variant | Border | Shadow | Padding | Usage |
|---------|--------|--------|---------|-------|
| **Default** | 1px `neutral-200` | `--shadow-sm` | 24px | General content |
| **Flat** | 1px `neutral-200` | none | 24px | Dense lists, portals |
| **Elevated** | none | `--shadow-md` | 24px | Marketing features |
| **Interactive** | 1px `neutral-200` | `--shadow-sm` → `--shadow-md` on hover | 24px | Clickable product cards |
| **Stat/KPI** | none | none | 20px | Dashboard metrics (bg `neutral-50`) |

### 8.2 Card Anatomy

```
┌─────────────────────────────────────┐
│ [Media/Image — optional]            │
│ [Eyebrow / Badge]                   │
│ [Title — heading-sm]                │
│ [Description — body-sm, neutral-500]│
│ [Meta row — caption]                │
│ [Actions — button group]            │
└─────────────────────────────────────┘
```

### 8.3 Card Sizes

| Size | Padding | Title Size |
|------|---------|------------|
| sm | 16px | heading-sm |
| md | 24px | heading-sm |
| lg | 32px | heading-md |

### 8.4 Specialized Cards

| Type | Spec |
|------|------|
| **Product card** | 48px product icon, accent top border 3px, feature list max 3 bullets |
| **Pricing card** | Highlighted tier: primary border 2px, "Popular" badge |
| **Testimonial** | Quote body-lg, avatar 48px, name + role caption |
| **Blog card** | 16:9 image, category badge, date caption |
| **Dashboard stat** | Metric display-md bold, delta badge (+/− semantic color), sparkline optional |

### 8.5 Card Grid

- Marketing: 3 columns (lg), 2 (md), 1 (sm); gap 24px
- Dashboard: 4 columns stats (lg), 2 (md), 1 (sm); gap 16px

---

## 9. Alerts

### 9.1 Alert Variants

| Variant | Icon | Background | Border Left |
|---------|------|------------|-------------|
| Info | info circle | `info-bg` | 4px `info-fg` |
| Success | check circle | `success-bg` | 4px `success-fg` |
| Warning | alert triangle | `warning-bg` | 4px `warning-fg` |
| Error | x circle | `error-bg` | 4px `error-fg` |

### 9.2 Alert Anatomy

```
[Icon] [Title — optional, semibold]
       [Message — body-sm]
       [Actions — link buttons, optional]
                                    [Dismiss ×]
```

### 9.3 Alert Sizes & Placement

| Type | Placement | Dismissible |
|------|-----------|-------------|
| **Inline/banner** | Within content flow | Yes |
| **Page-level** | Below header, full width | Yes |
| **Toast** | Bottom-right stack (portal) | Auto 5s + manual |
| **Persistent system** | Top of admin console | No (until resolved) |

### 9.4 Toast Spec

- Width: 360px max
- Stack gap: 8px
- Enter: slide up + fade (200ms)
- Exit: fade out (150ms)
- Max visible: 3; queue additional

---

## 10. Tables

### 10.1 Table Variants

| Variant | Usage |
|---------|-------|
| **Default** | General data |
| **Compact** | Admin dense views (row height 40px) |
| **Comfortable** | Customer portal (row height 52px) |
| **Striped** | Long scroll lists |
| **Borderless** | Embedded in cards |

### 10.2 Table Anatomy

```
[Toolbar: search | filters | bulk actions | column toggle]
┌──────────────────────────────────────────────────────────┐
│ ☐ │ Column A ▲ │ Column B   │ Column C   │ Actions      │
├───┼────────────┼────────────┼────────────┼──────────────┤
│ ☐ │ Cell       │ Cell       │ Badge      │ ⋮            │
│ ☐ │ Cell       │ Cell       │ Cell       │ ⋮            │
└──────────────────────────────────────────────────────────┘
[Pagination: Showing 1–25 of 340 | ← 1 2 3 ... → | Per page ▾]
```

### 10.3 Table Styling

| Element | Spec |
|---------|------|
| Header bg | `neutral-50` (light) / `neutral-800` (dark) |
| Header text | `--text-caption`, uppercase overline OR `--text-body-sm` semibold |
| Header height | 44px |
| Row height | 48px (default), 40px (compact) |
| Cell padding | 12px 16px |
| Border | Horizontal 1px `neutral-200` only |
| Hover row | `neutral-50` bg |
| Selected row | `primary-50` bg + primary left border 3px |

### 10.4 Sortable Columns

- Sort icon: chevron up/down, 14px, `neutral-400`; active sort `primary-600`
- Click header toggles asc/desc
- `aria-sort` attribute required

### 10.5 Responsive Tables

- **md and below:** Switch to card-list pattern (each row becomes stacked card)
- **Priority columns:** Hide lower-priority columns; expose via expand row or detail drawer
- Horizontal scroll only in admin with sticky first column (optional)

### 10.6 Empty & Loading States

- Empty: illustration 120px, message, CTA button centered in table area
- Loading: skeleton rows (5), shimmer animation
- Error: inline alert above table with retry action

---

## 11. Navigation

### 11.1 Public Site Header

**Height:** 72px (desktop), 64px (mobile)  
**Background:** `--surface-header` with bottom border 1px `neutral-200`  
**Behavior:** Sticky on scroll; subtle shadow after 10px scroll  
**Blur option:** `backdrop-filter: blur(8px)` at 90% opacity (marketing premium feel)

```
[Logo 140×32] [Products ▾] [Solutions ▾] [Customers] [Resources ▾] [Pricing]   [Search] [Login] [Start Free Trial]
```

| Element | Spec |
|---------|------|
| Logo | SVG, links to `/` |
| Nav links | `--text-body-sm`, `--font-medium`, `neutral-700`; hover `primary-600` |
| Active link | `primary-600`, 2px bottom border |
| Mega menu | Full-width panel, `--shadow-lg`, 3–4 columns, 32px padding |
| Search | Icon opens overlay input (md+); expandable on mobile |
| CTA button | Primary, sm size |

### 11.2 Mobile Navigation

- Hamburger icon right (or left per brand convention — right preferred)
- Full-screen drawer or slide-from-right panel
- Accordion for Products/Solutions/Resources
- CTA pinned to bottom of drawer
- Focus trap while open; Escape closes

### 11.3 Breadcrumbs

- Separator: chevron `/` 14px `neutral-400`
- Current page: `neutral-500`, not linked
- `--text-body-sm`
- Used in: portal, admin, product sub-pages

### 11.4 Tabs

| Variant | Indicator | Usage |
|---------|-----------|-------|
| **Underline** | 2px primary bottom border | Product sub-nav, settings |
| **Pill** | Filled bg `primary-50` | Filters, view toggles |
| **Bordered** | Card-style tab bar | Admin sections |

- Tab height: 40px
- Min tab width: 80px
- Keyboard: arrow keys navigate, manual activation

### 11.5 Pagination (Content)

- Numbered pages with prev/next
- Ellipsis for long ranges
- Current page: primary bg pill

---

## 12. Sidebars

### 12.1 Portal Sidebar (Customer & Partner)

**Width:** 260px expanded | 64px collapsed  
**Background:** `--surface-sidebar`  
**Border:** Right 1px `neutral-200`

```
┌──────────────────┐
│ [Logo mark]      │
│ [Org switcher ▾] │
├──────────────────┤
│ ◉ Dashboard      │
│ ○ My Products    │
│ ○ Billing        │
│ ○ Team           │
│ ○ Support        │
├──────────────────┤
│ ○ Settings       │
│ ○ Documentation ↗│
├──────────────────┤
│ [Avatar] User ▾  │
└──────────────────┘
```

### 12.2 Sidebar Item Spec

| State | Background | Text | Icon |
|-------|------------|------|------|
| Default | transparent | `neutral-600` | `neutral-500` |
| Hover | `neutral-100` | `neutral-800` | `neutral-700` |
| Active | `primary-50` | `primary-700` | `primary-600` |
| Disabled | transparent | `neutral-400` | `neutral-400` |

- Item height: 40px
- Padding: 8px 12px
- Icon: 20px, 12px gap to label
- Collapsed: icon only + tooltip on hover

### 12.3 Sidebar Sections

- Section label: `--text-overline`, `neutral-400`, 24px top margin, 8px bottom
- Dividers: 1px `neutral-200`, 16px vertical margin

### 12.4 Admin Sidebar

- Darker variant optional: bg `neutral-900`, text white/neutral-300
- Nested items: indent 16px per level
- Badge counts on items (e.g., pending approvals): pill badge sm

### 12.5 Responsive Sidebar

| Breakpoint | Behavior |
|------------|----------|
| ≥ lg | Fixed sidebar, collapsible toggle |
| md | Overlay drawer, hamburger trigger |
| sm | Full overlay drawer |

---

## 13. Footer

### 13.1 Public Site Footer

**Background:** `neutral-900` (light mode footer) / `neutral-950` `#020617` (dark)  
**Text:** `neutral-300` body, `neutral-100` headings  
**Padding:** 64px top, 32px bottom

```
┌─────────────────────────────────────────────────────────────────┐
│  [Logo]                    Products    Solutions    Company     │
│  Tagline one line          ─────────   ─────────   ─────────    │
│                            ChurchHub   Education    About       │
│  [LinkedIn][X][YouTube]    ERP Suite   Healthcare   Careers     │
│                            ...         ...           Contact     │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│  © 2026 Company Name    Privacy  Terms  Security  Cookies       │
│  [Language ▾]  [Region ▾]                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 13.2 Footer Link Spec

- Column heading: `--text-body-sm`, `--font-semibold`, `neutral-100`
- Links: `--text-body-sm`, `neutral-400`; hover `neutral-0` + underline
- Spacing: 32px between columns, 12px between links

### 13.3 Portal Footer

- Minimal: single row, `neutral-500` caption text
- Links: Help, Status, Privacy
- Fixed bottom optional on auth pages only

### 13.4 Admin Footer

- None (sidebar + header sufficient); version/build info in sidebar bottom

---

## 14. Hero Sections

### 14.1 Hero Variants

| Variant | Layout | Usage |
|---------|--------|-------|
| **Centered** | Text center, max-width 720px | Homepage, generic landing |
| **Split 50/50** | Copy left, media/illustration right | Product pages |
| **Split 40/60** | Copy left, product screenshot right | SaaS product heroes |
| **Background image** | Overlay gradient, text left | Industry solutions |
| **Minimal** | Heading + breadcrumb only | Inner pages |

### 14.2 Hero Sizing

| Element | Desktop | Mobile |
|---------|---------|--------|
| Section padding Y | 96px–128px | 48px–64px |
| Display heading | display-xl or display-lg | heading-xl |
| Lead text | body-lg, max 560px | body-md |
| CTA group gap | 16px | 12px stacked full-width buttons |
| Media | max 600px width | below copy, 100% width |

### 14.3 Hero Elements

| Element | Spec |
|---------|------|
| Eyebrow | overline, `primary-600`, optional product accent |
| Headline | display-lg, `neutral-900`, max 2 lines |
| Subheadline | body-lg, `neutral-600`, max 3 lines |
| Primary CTA | Button lg primary |
| Secondary CTA | Button lg secondary |
| Trust strip | Logo bar below CTAs, caption "Trusted by..." |
| Background | Subtle gradient mesh OR `neutral-50` with grid dot pattern |

### 14.4 Hero Background Patterns

- **Gradient mesh:** primary-50 → neutral-0 (light); primary-900/20 → page bg (dark)
- **Grid dots:** 24px spacing, 1px dots `neutral-200` at 40% opacity
- **No heavy photography** behind text without 60%+ overlay for contrast

### 14.5 Product Hero Accent

- 3px top border or left accent bar in product color
- Product icon 64px in eyebrow row
- Screenshot in browser chrome frame (optional decorative wrapper)

---

## 15. Icons

### 15.1 Icon System

**Library:** Lucide Icons (consistent stroke, MIT license)  
**Style:** Outline/stroke default; filled variant for active nav states only  
**Stroke width:** 1.5px (default), 2px (emphasis)

### 15.2 Icon Sizes

| Token | Size | Usage |
|-------|------|-------|
| `--icon-xs` | 14px | Inline text, badges |
| `--icon-sm` | 16px | Buttons sm, table actions |
| `--icon-md` | 20px | Nav items, inputs |
| `--icon-lg` | 24px | Section headers, empty states |
| `--icon-xl` | 32px | Feature blocks |
| `--icon-2xl` | 48px | Product icons, hero |

### 15.3 Icon Usage Rules

- Always pair with text label except icon-only buttons (require `aria-label`)
- Semantic icons: success check, warning triangle, error x — never rely on color alone
- Product icons: custom SVG mark inside 48px rounded square, product accent bg at 10% opacity
- External link: trailing ↗ 14px
- Loading: spinner (rotating circle), not hourglass

### 15.4 Icon Color

| Context | Color |
|---------|-------|
| Default | `neutral-500` |
| Interactive | inherits text color |
| Active nav | `primary-600` |
| Semantic | matches alert semantic fg |
| On primary button | white |

---

## 16. Dashboard Styles

### 16.1 Dashboard Layout Shell

```
┌────────┬────────────────────────────────────────────────┐
│        │ [Top bar: breadcrumb | search | notifications | avatar] │
│ Side   ├────────────────────────────────────────────────┤
│ bar    │ [Page title + actions]                         │
│        │ [Filter bar — optional]                        │
│        │ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│        │ │ Stat   │ │ Stat   │ │ Stat   │ │ Stat   │   │
│        │ └────────┘ └────────┘ └────────┘ └────────┘   │
│        │ ┌─────────────────────┐ ┌──────────────────┐   │
│        │ │ Main chart/table    │ │ Side panel       │   │
│        │ └─────────────────────┘ └──────────────────┘   │
└────────┴────────────────────────────────────────────────┘
```

### 16.2 Page Header (Dashboard)

- Title: `--text-heading-xl`
- Subtitle: `--text-body-sm`, `neutral-500`
- Actions: right-aligned button group (secondary + primary)
- Margin bottom: 24px

### 16.3 KPI / Stat Cards

| Element | Spec |
|---------|------|
| Label | caption, `neutral-500`, uppercase optional |
| Value | heading-lg or display-md, tabular-nums |
| Delta | badge sm: green +↑ / red +↓ with percentage |
| Sparkline | 64×24px, stroke primary-500, no axes |

### 16.4 Chart Placeholder Style

- Grid lines: `neutral-200`, dashed
- Axis labels: caption, `neutral-500`
- Data series: primary-600, product accent for multi-series
- Tooltip: raised surface, shadow-md, body-sm

### 16.5 Filter Bar

- Background: `neutral-50` or inline
- Controls: sm inputs, sm buttons
- Active filter pills: primary-50 bg, primary-700 text, dismiss ×

### 16.6 Activity Feed

- Timeline: 2px line `neutral-200`, dot 8px primary-600
- Item: avatar 32px, action text body-sm, timestamp caption
- Max items before "View all" link

### 16.7 Dashboard Density Toggle (Enterprise)

- Comfortable (default) vs Compact: reduces row heights and padding by 25%
- User preference persisted in local storage

---

## 17. Animations

### 17.1 Motion Principles

- **Purposeful:** Motion guides attention, never decorates
- **Fast:** Enterprise users prefer snappy over playful
- **Respectful:** Honor `prefers-reduced-motion`

### 17.2 Duration Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--duration-instant` | 0ms | Reduced motion fallback |
| `--duration-fast` | 100ms | Hover color, opacity |
| `--duration-normal` | 200ms | Dropdowns, tooltips, toasts |
| `--duration-slow` | 300ms | Modals, drawers, page transitions |
| `--duration-slower` | 500ms | Marketing hero entrance (optional) |

### 17.3 Easing Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--ease-default` | `cubic-bezier(0.4, 0, 0.2, 1)` | General |
| `--ease-in` | `cubic-bezier(0.4, 0, 1, 1)` | Exit |
| `--ease-out` | `cubic-bezier(0, 0, 0.2, 1)` | Enter |
| `--ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Micro-interactions (subtle) |

### 17.4 Standard Animations

| Animation | Spec |
|-----------|------|
| Button hover | background 100ms ease-default |
| Dropdown open | opacity 0→1 + translateY(-4px→0), 200ms ease-out |
| Modal open | backdrop fade 200ms; panel scale 0.95→1 + fade, 200ms |
| Drawer open | translateX(100%→0), 300ms ease-out |
| Toast enter | translateY(16px→0) + fade, 200ms |
| Skeleton shimmer | gradient sweep 1.5s infinite linear |
| Page transition (portal) | fade 150ms crossfade |
| Marketing scroll reveal | translateY(24px→0) + fade, 500ms, stagger 100ms per child |

### 17.5 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  /* All durations → 0ms; opacity-only transitions allowed at 100ms max */
}
```

- No parallax, no auto-playing carousels without pause control
- Essential feedback (focus, error shake) may use instant state change

---

## 18. Dark Mode

### 18.1 Strategy

- **Semantic tokens** mapped per theme — components never reference raw hex
- **Toggle:** User preference (portal/admin) + system preference (marketing)
- **Storage:** `localStorage.theme = light | dark | system`
- **Implementation:** `[data-theme="dark"]` on `<html>` element

### 18.2 Dark Mode Adjustments

| Element | Adjustment |
|---------|------------|
| Primary buttons | Use `primary-500` bg (lighter) for contrast |
| Borders | Increase visibility: `neutral-700` vs `neutral-200` |
| Shadows | Higher opacity, softer spread |
| Images | Optional `brightness(0.9)` on large photos |
| Elevation | Use surface lightness steps, not shadows alone |
| Code blocks | `neutral-800` bg |

### 18.3 What Does Not Change

- Layout, spacing, typography scale
- Component anatomy
- Icon shapes
- Motion timing

### 18.4 Theme Toggle UI

- Sun/moon icon button in header (portal, marketing footer)
- Switch in settings: Light | System | Dark (segmented control)
- Smooth crossfade 200ms on background-color and color (if reduced motion off)

---

## 19. Light Mode

### 19.1 Default Theme

Light mode is the **default** for marketing (max readability, print-friendly, enterprise convention).

### 19.2 Light Mode Character

- Clean white surfaces
- Slate text hierarchy
- Blue primary actions
- Subtle gray section alternation (`neutral-50`)
- Professional, airy marketing; structured, bordered portals

### 19.3 Light Mode Specifics

| Context | Treatment |
|---------|-----------|
| Marketing | White page, gray-50 sections, strong heading contrast |
| Portal | Gray-50 page bg, white cards (creates depth) |
| Admin | White page, bordered flat cards (density) |
| Forms | White inputs, gray-200 borders |
| Tables | White rows, gray-50 header |

---

## 20. Mobile Responsiveness

### 20.1 Touch Targets

- Minimum: **44×44px** (WCAG 2.5.5 AAA target; 40px absolute minimum)
- Spacing between targets: 8px minimum
- Full-width primary buttons on mobile forms and heroes

### 20.2 Responsive Patterns

| Component | Mobile Adaptation |
|-----------|-------------------|
| Header | Hamburger drawer |
| Mega menu | Accordion in drawer |
| Hero | Stack vertical; image below copy |
| Feature grid | 1 column |
| Pricing table | Horizontal scroll OR stacked cards |
| Footer | Accordion columns or 2-column grid |
| Sidebar | Overlay drawer |
| Tables | Card list pattern |
| Modals | Full-screen sheet on sm |
| Dashboard stats | 2×2 grid → 1 column |

### 20.3 Typography Scaling

| Token | Mobile Override |
|-------|-----------------|
| display-xl | display-lg |
| display-lg | heading-xl |
| heading-xl | heading-lg |
| Section padding Y | 50–60% of desktop |

### 20.4 Viewport & Safe Areas

- `viewport-fit=cover` with safe-area-inset padding for notched devices
- Sticky mobile CTA bar: 16px padding + safe-area-inset-bottom

### 20.5 Performance on Mobile

- Lazy load below-fold images
- No hover-dependent interactions
- Reduce motion on low-power mode (future: `prefers-reduced-data`)

---

## 21. Accessibility Standards

### 21.1 Compliance Target

**WCAG 2.1 Level AA** across all surfaces; AAA for contrast on body text where feasible.

### 21.2 Keyboard Navigation

| Requirement | Implementation |
|-------------|----------------|
| All interactive elements focusable | Native controls or `tabindex="0"` |
| Visible focus indicator | 2px ring, primary-500, 2px offset |
| Skip link | "Skip to main content" first focusable element |
| Trap focus | Modals, drawers |
| Escape closes | Overlays, dropdowns, mega menus |
| Logical tab order | DOM order matches visual order |

### 21.3 Screen Readers

- Semantic HTML: `<nav>`, `<main>`, `<aside>`, `<header>`, `<footer>`
- Landmarks: one `<main>` per page
- `aria-label` on icon-only buttons
- `aria-expanded` on toggles
- `aria-live="polite"` on toasts and dynamic alerts
- `role="status"` on loading indicators
- Form errors announced via `aria-describedby` + `role="alert"` on submit

### 21.4 Color & Visual

- Never convey information by color alone (icons, text labels accompany semantic colors)
- Focus not indicated by color alone (ring + offset)
- Text resize: support up to 200% zoom without horizontal scroll
- High contrast mode: `@media (forced-colors: active)` — use system colors, visible borders

### 21.5 Content Accessibility

- All images: meaningful `alt` or `alt=""` if decorative
- Video: captions required
- Link text: descriptive (no "click here")
- Language: `<html lang="en">` + `hreflang` alternates
- Reading level: plain language in UI microcopy

### 21.6 Form Accessibility

- Every input has associated `<label>` (not placeholder-only)
- Error identification: text + icon + `aria-invalid="true"`
- Autocomplete attributes on standard fields
- Group related fields with `<fieldset>` + `<legend>`

### 21.7 Testing Checklist

- [ ] axe DevTools: 0 critical/serious violations
- [ ] Keyboard-only walkthrough of all flows
- [ ] VoiceOver (macOS/iOS) + NVDA (Windows) smoke test
- [ ] 200% browser zoom check
- [ ] Color contrast audit (all text/background pairs)
- [ ] Reduced motion verification

---

## 22. Component State Matrix (Global)

Every interactive component supports:

| State | Required |
|-------|----------|
| Default | ✓ |
| Hover | ✓ |
| Focus | ✓ |
| Active | ✓ |
| Disabled | ✓ |
| Loading | Where async |
| Error | Where validation |
| Empty | Where data-driven |

---

## 23. Z-Index Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--z-base` | 0 | Default |
| `--z-dropdown` | 100 | Dropdowns, popovers |
| `--z-sticky` | 200 | Sticky header, table header |
| `--z-sidebar` | 250 | Fixed sidebar |
| `--z-overlay` | 300 | Drawer backdrop |
| `--z-modal` | 400 | Modals |
| `--z-toast` | 500 | Toasts |
| `--z-tooltip` | 600 | Tooltips |

---

## 24. Token File Reference

Implementation tokens live at:

- `frontend/shared-ui/tokens/tokens.css` — CSS custom properties (light + dark)
- `frontend/shared-ui/tokens/tokens.json` — Platform-agnostic token export

All components MUST consume semantic tokens only. Direct hex usage is prohibited in component styles.

---

## 25. Versioning & Governance

| Change Type | Version Bump | Approval |
|-------------|--------------|----------|
| Token value tweak (non-breaking) | Patch 1.0.x | Design lead |
| New component variant | Minor 1.x.0 | Design + Eng lead |
| Breaking token rename/removal | Major x.0.0 | Architecture review |
| New product accent color | Minor | Product marketing |

Document all changes in `docs/design-system/CHANGELOG.md`.

---

*End of Enterprise Design System v1.0.0*
