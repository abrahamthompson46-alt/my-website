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
        "description": "Microfinance platform for loans, savings, and collections — marketed here, running as its own product.",
        "features": ["Loan management", "Savings accounts", "Collections"],
    },
]

WHY_CHOOSE_US = [
    {
        "icon": "shield-check",
        "title": "Security you can open",
        "description": "Staff MFA, audit logging, CSRF protection, and a published Security Center — not slogans alone.",
        "url_name": "website:security",
    },
    {
        "icon": "layers",
        "title": "Modular live products",
        "description": "ChurchHub and CoreTrust are live applications today. Shared billing and portal sit on Zreta.",
        "url_name": "website:architecture",
    },
    {
        "icon": "globe",
        "title": "Built for African organizations",
        "description": (
            "GHS pricing, Mobile Money via Hubtel/Paystack/Flutterwave, and human onboarding — "
            "capabilities we actually publish, not slogans."
        ),
        "url_name": "website:payments_platform",
    },
    {
        "icon": "activity",
        "title": "Enterprise reliability — defined",
        "description": "See what Zreta publishes on access control, backups, status, and support targets.",
        "url_name": "website:reliability",
    },
]

INDUSTRIES = [
    {
        "name": "Faith Organizations",
        "icon": "church",
        "description": "Churches and ministries connecting members, giving, and community programs.",
        "products": ["ChurchHub · Live"],
        "url_name": "website:solution_churches",
    },
    {
        "name": "Financial Services",
        "icon": "landmark",
        "description": "Microfinance institutions, SACCOs, and cooperatives running core banking with CoreTrust.",
        "products": ["CoreTrust · Live"],
        "url_name": "website:solution_microfinance",
    },
    {
        "name": "Education",
        "icon": "graduation-cap",
        "description": "Schools and training centers — School Management is on the roadmap.",
        "products": ["Roadmap"],
        "url_name": "website:solution_education",
    },
    {
        "name": "Healthcare",
        "icon": "heart-pulse",
        "description": "Clinics and hospitals — Hospital Management is on the roadmap.",
        "products": ["Roadmap"],
        "url_name": "website:solution_healthcare",
    },
]

TESTIMONIALS = []

LATEST_NEWS = []

STATISTICS = [
    {"value": "30 days", "label": "ChurchHub free trial"},
    {"value": "Demo", "label": "CoreTrust starts with a demo"},
    {"value": "GHS", "label": "Local pricing available"},
    {"value": "2", "label": "Live products today"},
]

TRUST_SIGNALS = [
    {
        "icon": "shield-check",
        "title": "Security",
        "description": "Staff MFA, audit logging, and a published Security Center.",
        "url_name": "website:security",
    },
    {
        "icon": "smartphone",
        "title": "Payments",
        "description": "GHS plans where listed; Hubtel, Paystack, and Flutterwave ready.",
        "url_name": "website:payments_platform",
    },
    {
        "icon": "activity",
        "title": "Operations",
        "description": "Published system status and support response targets.",
        "url_name": "website:status",
    },
    {
        "icon": "layers",
        "title": "Architecture",
        "description": "Zreta shared billing/security layer with live ChurchHub and CoreTrust apps.",
        "url_name": "website:architecture",
    },
]

TRUST_STRIP = [
    {"icon": "credit-card", "label": "GHS pricing"},
    {"icon": "smartphone", "label": "Mobile Money"},
    {"icon": "shield-check", "label": "Staff MFA"},
    {"icon": "life-buoy", "label": "24h support target"},
]

HERO = {
    "eyebrow": "Enterprise software platform",
    "headline": "Zreta",
    "headline_line1": "Zreta",
    "headline_line2": "Enterprise software for organizations that scale",
    "subheadline": (
        "Build operations on secure, modular software — starting with live ChurchHub "
        "and CoreTrust, with shared billing, portal access, and published security practices."
    ),
    "trust_text": "ChurchHub: 30-day trial · CoreTrust: request a demo · GHS pricing",
    "product_pills": ["ChurchHub · Live", "CoreTrust · Live"],
    "cta_primary_label": "Explore products",
    "cta_primary_url": "/products/",
    "cta_secondary_label": "Request a demo",
    "cta_secondary_url": "#request-demo",
}

CTA = {
    "title": "Ready to evaluate a live product?",
    "subtitle": "ChurchHub and CoreTrust are live. Start on the product site, then manage billing in Zreta.",
}

START_TRIAL = {
    "eyebrow": "Start trial",
    "title": "Start on the live product",
    "subtitle": (
        "Choose ChurchHub to create an account on its signup page, or continue to "
        "CoreTrust to begin with the product team."
    ),
}

REQUEST_DEMO = {
    "eyebrow": "Request a demo",
    "title": "See a guided walkthrough",
    "subtitle": (
        "Pick ChurchHub or CoreTrust and continue on its product site to request a demo."
    ),
}

HOW_IT_WORKS = [
    {
        "title": "Choose a product",
        "description": "Browse ChurchHub, CoreTrust, and other modular solutions for your industry.",
    },
    {
        "title": "Start trial or request a demo",
        "description": "Continue to the live product site to create an account or request a demo.",
    },
    {
        "title": "Manage billing in Zreta",
        "description": "Use your customer portal for subscriptions, invoices, and launch links.",
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
        "start_trial_section": START_TRIAL,
        "request_demo_section": REQUEST_DEMO,
        "how_it_works": HOW_IT_WORKS,
        "newsletter_section": NEWSLETTER,
        "show_testimonials": False,
        "show_latest_news": False,
    }
