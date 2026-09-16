"""
Central navigation configuration.
Import and extend these structures — do not hardcode nav in templates.
"""

PUBLIC_HEADER_NAV = [
    {
        "label": "Products",
        "key": "products",
        "type": "mega",
        "columns": [
            {
                "title": "Live now",
                "links": [
                    {"label": "ChurchHub", "url_name": "products:detail", "url_kwargs": {"slug": "churchhub"}, "accent": "churchhub"},
                    {"label": "CoreTrust", "url_name": "products:detail", "url_kwargs": {"slug": "microfinance-core"}, "accent": "microfinance"},
                    {"label": "All products", "url_name": "products:list"},
                ],
            },
            {
                "title": "Roadmap",
                "links": [
                    {"label": "ERP Suite", "url_name": "products:detail", "url_kwargs": {"slug": "erp-suite"}, "accent": "erp"},
                    {"label": "School Management", "url_name": "products:detail", "url_kwargs": {"slug": "school-management"}, "accent": "school"},
                    {"label": "Hospital Management", "url_name": "products:detail", "url_kwargs": {"slug": "hospital-management"}, "accent": "hospital"},
                    {"label": "HR & Payroll", "url_name": "products:detail", "url_kwargs": {"slug": "hr-payroll"}, "accent": "hr"},
                ],
            },
            {
                "title": "Get started",
                "links": [
                    {"label": "Request a demo", "url": "/#request-demo"},
                    {"label": "Start free trial", "url": "/#start-trial"},
                    {"label": "Pricing", "url_name": "products:list"},
                ],
            },
        ],
    },
    {
        "label": "Solutions",
        "key": "solutions",
        "type": "mega",
        "columns": [
            {
                "title": "By industry",
                "links": [
                    {"label": "Churches", "url_name": "website:solution_churches"},
                    {"label": "Microfinance", "url_name": "website:solution_microfinance"},
                    {"label": "Enterprises", "url_name": "website:solution_enterprises"},
                    {"label": "Education", "url_name": "website:solution_education"},
                    {"label": "Healthcare", "url_name": "website:solution_healthcare"},
                ],
            },
        ],
    },
    {
        "label": "Platform",
        "key": "platform",
        "type": "mega",
        "columns": [
            {
                "title": "Capabilities",
                "links": [
                    {"label": "Architecture", "url_name": "website:architecture"},
                    {"label": "Security Center", "url_name": "website:security"},
                    {"label": "Payments & billing", "url_name": "website:payments_platform"},
                    {"label": "API & integrations", "url_name": "website:integrations"},
                    {"label": "System status", "url_name": "website:status"},
                ],
            },
        ],
    },
    {
        "label": "Resources",
        "key": "resources",
        "type": "mega",
        "columns": [
            {
                "title": "Learn",
                "links": [
                    {"label": "Blog & guides", "url_name": "marketing:blog_list"},
                    {"label": "Documentation", "url_name": "documentation:index"},
                    {"label": "White papers", "url_name": "marketing:whitepapers"},
                    {"label": "Support", "url_name": "support:index"},
                    {"label": "FAQs", "url_name": "cms:faq_list"},
                ],
            },
        ],
    },
    {"label": "Pricing", "url_name": "products:list"},
]

PUBLIC_FOOTER_COLUMNS = [
    {
        "title": "Products",
        "links": [
            {"label": "ChurchHub", "url_name": "products:detail", "url_kwargs": {"slug": "churchhub"}},
            {"label": "CoreTrust", "url_name": "products:detail", "url_kwargs": {"slug": "microfinance-core"}},
            {"label": "All products", "url_name": "products:list"},
        ],
    },
    {
        "title": "Solutions",
        "links": [
            {"label": "Churches", "url_name": "website:solution_churches"},
            {"label": "Microfinance", "url_name": "website:solution_microfinance"},
            {"label": "Enterprises", "url_name": "website:solution_enterprises"},
        ],
    },
    {
        "title": "Platform",
        "links": [
            {"label": "Architecture", "url_name": "website:architecture"},
            {"label": "Security Center", "url_name": "website:security"},
            {"label": "Support", "url_name": "support:index"},
            {"label": "SLA", "url_name": "website:sla"},
            {"label": "System status", "url_name": "website:status"},
        ],
    },
    {
        "title": "Company",
        "links": [
            {"label": "About", "url_name": "pages:about"},
            {"label": "Contact", "url_name": "contact:form"},
            {"label": "Careers", "url_name": "careers:list"},
            {"label": "Enterprise onboarding", "url_name": "website:onboarding"},
        ],
    },
    {
        "title": "Legal",
        "links": [
            {"label": "Privacy", "url_name": "website:privacy"},
            {"label": "Privacy Center", "url_name": "website:privacy_center"},
            {"label": "Terms", "url_name": "website:terms"},
            {"label": "Security", "url_name": "website:security"},
            {"label": "Enterprise readiness", "url_name": "website:enterprise"},
            {"label": "Business continuity", "url_name": "website:continuity"},
            {"label": "Refund Policy", "url_name": "website:refund"},
        ],
    },
]

CUSTOMER_PORTAL_NAV = [
    {"label": "Dashboard", "url_name": "customer_portal:dashboard", "icon": "layout-dashboard"},
    {"label": "Subscriptions", "url_name": "customer_portal:subscriptions", "icon": "repeat"},
    {"label": "Licenses", "url_name": "customer_portal:licenses", "icon": "key"},
    {"label": "Invoices", "url_name": "customer_portal:invoices", "icon": "receipt", "active_on": ["customer_portal:invoices", "customer_portal:invoice_detail"]},
    {"label": "Payments", "url_name": "payments:list", "icon": "credit-card", "active_on": ["payments:list", "payments:detail", "payments:checkout"]},
    {"label": "Downloads", "url_name": "customer_portal:downloads", "icon": "download"},
    {"section": "Support & Resources"},
    {"label": "Support Tickets", "url_name": "customer_portal:tickets", "icon": "life-buoy", "active_on": ["customer_portal:tickets", "customer_portal:ticket_detail", "customer_portal:ticket_create"]},
    {"label": "Product Updates", "url_name": "customer_portal:updates", "icon": "sparkles"},
    {"label": "Documentation", "url_name": "customer_portal:documentation", "icon": "book-open"},
    {"section": "Account"},
    {"label": "Notifications", "url_name": "customer_portal:notifications", "icon": "bell"},
    {"label": "Profile", "url_name": "customer_portal:profile", "icon": "user"},
    {"label": "Security", "url_name": "customer_portal:security", "icon": "shield"},
]

OPERATIONS_NAV = [
    {"label": "Dashboard", "url_name": "operations:dashboard", "icon": "layout-dashboard"},
    {"label": "Analytics", "url_name": "operations:analytics", "icon": "bar-chart-2"},
    {"section": "Business"},
    {"label": "Products", "url_name": "operations:products", "icon": "package"},
    {"label": "Customers", "url_name": "operations:customers", "icon": "users"},
    {"label": "Leads", "url_name": "operations:leads", "icon": "user-plus"},
    {"label": "Demo Requests", "url_name": "operations:demo_requests", "icon": "calendar"},
    {"label": "Payments", "url_name": "operations:payments", "icon": "credit-card"},
    {"section": "Operations"},
    {"label": "Support", "url_name": "operations:support", "icon": "life-buoy"},
    {"label": "Documentation", "url_name": "operations:documentation", "icon": "book-open"},
    {"label": "Marketing", "url_name": "operations:marketing", "icon": "megaphone"},
    {"section": "Platform"},
    {"label": "Control Room", "url_name": "control_room:dashboard", "icon": "sliders"},
    {"label": "System Health", "url_name": "operations:system_health", "icon": "activity"},
    {"label": "Activity Logs", "url_name": "operations:activity", "icon": "list"},
]

PARTNER_PORTAL_NAV = [
    {"label": "Dashboard", "url_name": "partners:dashboard", "icon": "layout-dashboard"},
    {"label": "Referrals", "url_name": "partners:dashboard", "icon": "share-2"},
    {"label": "Deal Registration", "url_name": "partners:dashboard", "icon": "file-check"},
    {"label": "Marketing Assets", "url_name": "partners:dashboard", "icon": "image"},
    {"label": "Commissions", "url_name": "partners:dashboard", "icon": "dollar-sign"},
    {"section": "Account"},
    {"label": "Settings", "url_name": "partners:dashboard", "icon": "settings"},
    {"label": "Support", "url_name": "support:index", "icon": "life-buoy"},
]

CONTROL_ROOM_NAV = [
    {"label": "Super Dashboard", "url_name": "control_room:dashboard", "icon": "layout-dashboard"},
    {"section": "Platform"},
    {"label": "Platform Setup", "url_name": "control_room:setup", "icon": "database"},
    {"label": "Site Settings", "url_name": "control_room:settings", "icon": "settings"},
    {"label": "Platform Ops", "url_name": "control_room:platform_ops", "icon": "server", "owner_only": True},
    {"label": "Team & Access", "url_name": "control_room:team", "icon": "users"},
    {"label": "Navigation", "url_name": "control_room:navigation", "icon": "menu"},
    {"label": "Redirects", "url_name": "control_room:redirects", "icon": "external-link"},
    {"label": "Announcements", "url_name": "control_room:announcements", "icon": "bell"},
    {"label": "Feature Flags", "url_name": "control_room:flags", "icon": "zap"},
    {"section": "Catalog"},
    {"label": "Products", "url_name": "control_room:products", "icon": "package"},
    {"section": "Content"},
    {"label": "Content Hub", "url_name": "control_room:content", "icon": "layers"},
    {"label": "Documentation", "url_name": "control_room:documentation", "icon": "file-text"},
    {"section": "Operations"},
    {"label": "Ops Dashboard", "url_name": "operations:dashboard", "icon": "bar-chart-2"},
    {"label": "Change Log", "url_name": "control_room:changelog", "icon": "list"},
    {"section": "Advanced"},
    {"label": "Content Manager", "url_name": "admin:index", "icon": "settings", "external": True},
]
