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
        "title": "Enterprise-grade security",
        "description": "SOC 2-ready infrastructure, encryption at rest and in transit, and role-based access control.",
    },
    {
        "icon": "layers",
        "title": "Modular by design",
        "description": "Start with one product and expand seamlessly. Shared identity, billing, and data across the suite.",
    },
    {
        "icon": "globe",
        "title": "Built for Africa & beyond",
        "description": "Multi-currency, offline-capable modules, and local compliance for regional markets.",
    },
    {
        "icon": "headphones",
        "title": "24/7 expert support",
        "description": "Dedicated onboarding, training, and priority support with guaranteed response SLAs.",
    },
    {
        "icon": "zap",
        "title": "Rapid deployment",
        "description": "Go live in weeks, not months. Pre-built templates and migration tools accelerate adoption.",
    },
    {
        "icon": "bar-chart",
        "title": "Actionable analytics",
        "description": "Real-time dashboards and exportable reports to drive data-informed decisions.",
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
        "quote": "We consolidated five legacy systems into one platform. Our team saves 20 hours per week on reporting alone.",
        "name": "Sarah Okonkwo",
        "role": "CFO",
        "company": "Unity Microfinance",
        "initials": "SO",
    },
    {
        "quote": "ChurchHub transformed how we engage our 3,000-member congregation. Giving increased 35% in the first year.",
        "name": "Rev. James Mwangi",
        "role": "Senior Pastor",
        "company": "Grace Community Church",
        "initials": "JM",
    },
    {
        "quote": "The School Management platform reduced fee collection delays by 60%. Parents love the mobile portal.",
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
        "title": "Enterprise Platform achieves SOC 2 Type II certification",
        "category": "Company",
        "date": "June 28, 2026",
        "read_time": "3 min read",
        "excerpt": "Our commitment to security and compliance continues with independent third-party validation.",
    },
]

STATISTICS = [
    {"value": "2,500+", "label": "Organizations served"},
    {"value": "18", "label": "Countries worldwide"},
    {"value": "99.9%", "label": "Platform uptime SLA"},
    {"value": "4.8/5", "label": "Customer satisfaction"},
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
    "eyebrow": "Enterprise SaaS Platform",
    "headline": "Software that powers organizations across every industry",
    "subheadline": (
        "From churches to hospitals, schools to microfinance — one trusted platform "
        "delivering modular products built for scale, security, and regional compliance."
    ),
    "trust_text": "Trusted by 2,500+ organizations worldwide",
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
