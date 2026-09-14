"""Fallback homepage content when CMS data is not yet seeded."""

FEATURED_PRODUCTS = [
    {
        "name": "ChurchHub",
        "slug": "churchhub",
        "accent": "churchhub",
        "tagline": "All-in-one platform for faith communities",
        "description": "Manage members, giving, events, groups, and communications from a single dashboard.",
        "features": ["Member management", "Online giving", "Event planning"],
    },
    {
        "name": "CoreTrust",
        "slug": "microfinance-core",
        "accent": "finance",
        "tagline": "Core banking for microfinance institutions",
        "description": "Live MFI platform for loans, savings, and collections — marketed here, running as its own product.",
        "features": ["Loan management", "Savings accounts", "Collections"],
    },
]

WHY_CHOOSE_US = [
    {
        "icon": "shield-check",
        "title": "Security-first platform",
        "description": "Email verification, staff MFA, audit logging, CSRF protection, and published security documentation.",
    },
    {
        "icon": "layers",
        "title": "Modular by design",
        "description": "Choose the products you need — ChurchHub, CoreTrust, and more — each with shared billing, portal, and support on Zreta.",
    },
    {
        "icon": "globe",
        "title": "Built for Africa & beyond",
        "description": "GHS pricing, regional payment gateways, and workflows designed for emerging markets.",
    },
    {
        "icon": "headphones",
        "title": "Human onboarding",
        "description": "Self-serve trials plus guided demos and support tickets with published response targets.",
    },
    {
        "icon": "zap",
        "title": "Fast time to value",
        "description": "Start a 30-day trial from any product page and access your customer portal after verification.",
    },
    {
        "icon": "bar-chart",
        "title": "Operations visibility",
        "description": "Control Room and Ops dashboards for demos, subscriptions, and platform activity.",
    },
]

INDUSTRIES = [
    {
        "name": "Faith Organizations",
        "icon": "church",
        "description": "Churches and ministries connecting members, giving, and community programs.",
        "products": ["ChurchHub"],
    },
    {
        "name": "Financial Services",
        "icon": "landmark",
        "description": "Microfinance institutions, SACCOs, and cooperatives running core banking with CoreTrust.",
        "products": ["CoreTrust"],
    },
    {
        "name": "Education",
        "icon": "graduation-cap",
        "description": "Schools and training centers managing admissions, fees, and parent engagement.",
        "products": ["School Management"],
    },
    {
        "name": "Healthcare",
        "icon": "heart-pulse",
        "description": "Clinics and hospitals with appointments, billing, and patient records.",
        "products": ["Hospital Management"],
    },
]

TESTIMONIALS = []

LATEST_NEWS = []

STATISTICS = [
    {"value": "30 days", "label": "Free trial on every plan"},
    {"value": "GHS", "label": "Local pricing available"},
    {"value": "24h", "label": "Support response target"},
    {"value": "3+", "label": "Payment gateway options"},
]

TRUST_SIGNALS = [
    {"icon": "credit-card", "title": "GHS pricing", "description": "Transparent plans in Ghanaian cedi where listed."},
    {"icon": "smartphone", "title": "Mobile Money ready", "description": "Hubtel, Paystack, and Flutterwave integrations."},
    {"icon": "shield-check", "title": "Staff MFA", "description": "Multi-factor authentication for platform administrators."},
    {"icon": "lock", "title": "Security overview", "description": "Published security, privacy, and status pages."},
]

TRUST_STRIP = [
    {"icon": "credit-card", "label": "GHS pricing"},
    {"icon": "smartphone", "label": "Mobile Money"},
    {"icon": "shield-check", "label": "Staff MFA"},
    {"icon": "life-buoy", "label": "24h support target"},
]

HERO = {
    "eyebrow": "Zreta · Modular enterprise software",
    "headline": "Enterprise software for organizations that need to scale",
    "headline_line1": "Enterprise software for",
    "headline_line2": "organizations that scale",
    "subheadline": (
        "Zreta markets and sells modular products for growing organizations — "
        "ChurchHub, CoreTrust, and more — with shared billing, security, and support. "
        "Each live product runs as its own application."
    ),
    "trust_text": "30-day free trial · GHS pricing · Mobile Money payments · Published security pages",
    "product_pills": [
        "ChurchHub",
        "CoreTrust",
        "ERP & operations",
        "School & hospital suites",
    ],
    "cta_primary_label": "Explore products",
    "cta_secondary_label": "Start free trial",
    "cta_secondary_url": "#start-trial",
}

CTA = {
    "title": "Ready to modernize your operations?",
    "subtitle": "Browse products and start a 30-day free trial — no credit card required.",
}

REQUEST_DEMO = {
    "eyebrow": "Get started",
    "title": "Start your 30-day free trial",
    "subtitle": (
        "Pick a product, create your account, and launch from the customer portal — "
        "no demo request or sales call required."
    ),
}

HOW_IT_WORKS = [
    {
        "title": "Choose a product",
        "description": "Browse modular solutions for faith, finance, education, healthcare, and operations.",
    },
    {
        "title": "Start your trial",
        "description": "Create an account and activate a 30-day trial from any product page — no credit card required.",
    },
    {
        "title": "Launch from your portal",
        "description": "Configure settings, invite your team, and upgrade when you're ready.",
    },
]

NEWSLETTER = {
    "title": "Product updates from Zreta",
    "subtitle": "Occasional notes on new products, platform improvements, and rollout news.",
}


def get_homepage_context():
    return {
        "hero": HERO,
        "why_choose_us": WHY_CHOOSE_US,
        "industries": INDUSTRIES,
        "testimonials": TESTIMONIALS,
        "latest_news": LATEST_NEWS,
        "statistics": STATISTICS,
        "trust_signals": TRUST_SIGNALS,
        "trust_strip": TRUST_STRIP,
        "cta_section": CTA,
        "start_trial_section": REQUEST_DEMO,
        "request_demo_section": REQUEST_DEMO,
        "how_it_works": HOW_IT_WORKS,
        "newsletter_section": NEWSLETTER,
        "show_testimonials": False,
        "show_latest_news": False,
    }
