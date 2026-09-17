"""Honest product-page depth sections (platform vs external product)."""

PRODUCT_DEPTH = {
    "churchhub": {
        "external_notice": (
            "ChurchHub is a live product application. Zreta markets and bills it; "
            "membership, giving, and church administration run on the ChurchHub site."
        ),
        "modules": [
            "Members & households",
            "Giving & remittance",
            "Events & groups",
            "Communications",
            "Roles & access",
            "Reports",
            "Billing via Zreta",
        ],
        "sections": [
            {
                "title": "Membership & households",
                "body": "Keep member and household records current with role-appropriate access for pastors, clerks, and members.",
                "scope": "external",
            },
            {
                "title": "Giving & accountability",
                "body": "Track giving and remittance with clearer financial accountability for church treasurers.",
                "scope": "external",
            },
            {
                "title": "Church operations",
                "body": "Coordinate events, groups, and day-to-day church administration in ChurchHub.",
                "scope": "external",
            },
            {
                "title": "Billing & portal (Zreta)",
                "body": "Subscriptions, invoices, payment proofs, and launch links are managed in the Zreta customer portal.",
                "scope": "platform",
            },
        ],
    },
    "microfinance-core": {
        "external_notice": (
            "CoreTrust is Zreta’s live microfinance product. Loan, savings, and collections "
            "workflows run in the CoreTrust application — not inside this marketing monolith."
        ),
        "modules": [
            "Customers",
            "Savings",
            "Loans",
            "Credit",
            "Collections",
            "Accounting",
            "Branches",
            "Reports",
            "Audit",
            "Security",
            "Billing via Zreta",
        ],
        "sections": [
            {
                "title": "Customers & branches",
                "body": "Maintain customer records and branch operations inside CoreTrust for MFIs, SACCOs, and cooperatives.",
                "scope": "external",
            },
            {
                "title": "Savings & credit",
                "body": "Operate savings products and credit workflows in the CoreTrust application.",
                "scope": "external",
            },
            {
                "title": "Loan lifecycle & collections",
                "body": "Digitize applications through repayment and coordinate collections and operational reporting.",
                "scope": "external",
            },
            {
                "title": "Accounting, reports & audit",
                "body": "Use CoreTrust as the operational system of record for accounting views, reports, and audit trails owned by that product.",
                "scope": "external",
            },
            {
                "title": "Security posture (honest)",
                "body": "Zreta publishes platform security and billing controls. Product-specific regulatory certifications and CoreTrust app security details are owned by the CoreTrust deployment.",
                "scope": "external",
            },
            {
                "title": "Billing & portal (Zreta)",
                "body": "Commercial subscriptions and invoices for CoreTrust are handled through Zreta when purchased here.",
                "scope": "platform",
            },
        ],
    },
}


def get_product_depth(slug: str):
    return PRODUCT_DEPTH.get(slug)
