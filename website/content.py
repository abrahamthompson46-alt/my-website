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
        "description": "Start with ChurchHub today and add more products as your organization grows.",
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
        "description": "Start a 14-day trial from pricing pages and access your customer portal after verification.",
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
        "description": "Microfinance institutions, SACCOs, and cooperatives running core banking operations.",
        "products": ["Microfinance Core"],
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
    {"value": "14 days", "label": "Free trial on every plan"},
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
    "eyebrow": "ChurchHub by Zreta",
    "headline": "Modern software for faith communities and growing organizations",
    "headline_line1": "Modern software for",
    "headline_line2": "faith communities",
    "subheadline": (
        "ChurchHub is live today — members, giving, events, and communications in one place. "
        "More modular products are rolling out on the same secure Zreta platform."
    ),
    "trust_text": "14-day free trial · GHS pricing · Mobile Money payments · Published security pages",
    "product_pills": ["ChurchHub", "Member directory", "Online giving", "Events"],
    "cta_primary_label": "Start ChurchHub trial",
    "cta_secondary_label": "Request a demo",
}

CTA = {
    "title": "Ready to modernize your operations?",
    "subtitle": "Start a free trial or book a demo — no credit card required for trials.",
}

REQUEST_DEMO = {
    "eyebrow": "Request a Demo",
    "title": "See ChurchHub in action",
    "subtitle": "Schedule a walkthrough with our team. We'll show you members, giving, events, and how Zreta fits your organization.",
}

NEWSLETTER = {
    "title": "Product updates from Zreta",
    "subtitle": "Occasional notes on ChurchHub features, platform improvements, and rollout news.",
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
        "request_demo_section": REQUEST_DEMO,
        "newsletter_section": NEWSLETTER,
        "show_testimonials": False,
        "show_latest_news": False,
    }
