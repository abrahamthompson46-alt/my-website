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
        "name": "Microfinance Core",
        "slug": "microfinance-core",
        "accent": "microfinance",
        "tagline": "Core banking for microfinance institutions",
        "description": "End-to-end loan lifecycle, savings, collections, and regulatory reporting built for scale.",
        "features": ["Loan management", "Savings accounts", "Collections & reporting"],
    },
    {
        "name": "ERP Suite",
        "slug": "erp-suite",
        "accent": "erp",
        "tagline": "Unified operations for growing enterprises",
        "description": "Finance, inventory, procurement, and CRM integrated in one modular ERP platform.",
        "features": ["Financial management", "Inventory control", "Procurement"],
    },
    {
        "name": "School Management",
        "slug": "school-management",
        "accent": "school",
        "tagline": "Modern administration for educational institutions",
        "description": "Admissions, academics, fees, attendance, and parent engagement — streamlined.",
        "features": ["Admissions", "Fee management", "Parent portal"],
    },
    {
        "name": "Hospital Management",
        "slug": "hospital-management",
        "accent": "hospital",
        "tagline": "Healthcare operations, simplified",
        "description": "Appointments, billing, pharmacy, lab, and patient records in a compliant platform.",
        "features": ["Appointments", "Billing & claims", "Pharmacy & lab"],
    },
    {
        "name": "HR & Payroll",
        "slug": "hr-payroll",
        "accent": "hr",
        "tagline": "People operations for modern organizations",
        "description": "Employee records, payroll processing, leave, recruitment, and performance in one system.",
        "features": ["Payroll automation", "Leave management", "Recruitment"],
    },
]

WHY_CHOOSE_US = [
    {
        "icon": "shield-check",
        "title": "Security-first platform",
        "description": "Email verification, staff MFA, audit logging, CSRF protection, and production security headers.",
    },
    {
        "icon": "layers",
        "title": "Modular by design",
        "description": "Start with one product and expand seamlessly. Shared identity, billing, and data across the suite.",
    },
    {
        "icon": "globe",
        "title": "Built for Africa & beyond",
        "description": "Multi-currency pricing, regional payment gateways, and workflows designed for emerging markets.",
    },
    {
        "icon": "headphones",
        "title": "Human onboarding",
        "description": "Self-serve trials plus guided demos and support tickets with published response targets.",
    },
    {
        "icon": "zap",
        "title": "Fast time to value",
        "description": "Start a 14-day trial from any pricing page and access your customer portal immediately after verification.",
    },
    {
        "icon": "bar-chart",
        "title": "Actionable analytics",
        "description": "Operations dashboards for demos, revenue, subscriptions, and product activity.",
    },
]

INDUSTRIES = [
    {
        "name": "Education",
        "icon": "graduation-cap",
        "description": "Schools, universities, and training centers managing admissions to alumni.",
        "products": ["School Management", "HR & Payroll"],
    },
    {
        "name": "Healthcare",
        "icon": "heart-pulse",
        "description": "Hospitals, clinics, and health networks with integrated patient care workflows.",
        "products": ["Hospital Management", "ERP Suite"],
    },
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
        "products": ["Microfinance Core", "ERP Suite"],
    },
]

TESTIMONIALS = [
    {
        "quote": "The platform helped us consolidate operations and respond to demo requests much faster.",
        "name": "Sarah Okonkwo",
        "role": "CFO",
        "company": "Unity Microfinance",
        "initials": "SO",
    },
    {
        "quote": "ChurchHub gave our team one place for members, giving, and events.",
        "name": "Rev. James Mwangi",
        "role": "Senior Pastor",
        "company": "Grace Community Church",
        "initials": "JM",
    },
    {
        "quote": "Parents appreciate the portal, and our admin team spends less time on manual follow-ups.",
        "name": "Dr. Amina Hassan",
        "role": "Principal",
        "company": "Horizon Academy",
        "initials": "AH",
    },
]

LATEST_NEWS = [
    {
        "title": "Introducing Hospital Management 2.0 with enhanced EMR workflows",
        "category": "Product Update",
        "date": "July 15, 2026",
        "read_time": "4 min read",
        "excerpt": "New patient timeline, lab integrations, and insurance billing automation are now generally available.",
    },
    {
        "title": "How microfinance institutions scale with cloud-native core banking",
        "category": "Guide",
        "date": "July 8, 2026",
        "read_time": "7 min read",
        "excerpt": "A practical framework for migrating from legacy systems without disrupting daily operations.",
    },
    {
        "title": "Publishing our security overview and status page",
        "category": "Company",
        "date": "June 28, 2026",
        "read_time": "3 min read",
        "excerpt": "Transparent documentation of platform controls, support SLAs, and live health checks.",
    },
]

STATISTICS = [
    {"value": "7", "label": "Modular products"},
    {"value": "14 days", "label": "Free trial on every plan"},
    {"value": "24h", "label": "Support response target"},
    {"value": "3", "label": "Payment gateway options"},
]

PARTNER_LOGOS = [
    {"name": "AfriTech Partners"},
    {"name": "CloudScale Systems"},
    {"name": "FinServe Alliance"},
    {"name": "EduGlobal Network"},
    {"name": "HealthFirst Group"},
    {"name": "Innovate Africa"},
]

HERO = {
    "eyebrow": "Zreta Enterprise Platform",
    "headline": "Software built for every organization",
    "headline_line1": "Software built for",
    "headline_line2": "every organization",
    "subheadline": (
        "ChurchHub, Microfinance Core, and ERP Suite — modular products on one trusted "
        "platform, built for scale, security, and compliance across Africa and beyond."
    ),
    "trust_text": "Self-serve trials · Transparent pricing · Published security & status pages",
    "product_pills": ["ChurchHub", "Microfinance Core", "ERP Suite"],
}


def get_homepage_context():
    return {
        "hero": HERO,
        "why_choose_us": WHY_CHOOSE_US,
        "industries": INDUSTRIES,
        "testimonials": TESTIMONIALS,
        "latest_news": LATEST_NEWS,
        "statistics": STATISTICS,
        "partner_logos": PARTNER_LOGOS,
    }
