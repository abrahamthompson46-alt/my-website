"""Honest product-page depth sections (platform vs external product)."""

PRODUCT_DEPTH = {
    "churchhub": {
        "external_notice": (
            "ChurchHub is a live product application. Zreta markets and bills it; "
            "membership, giving, and church administration run on the ChurchHub site."
        ),
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
        "sections": [
            {
                "title": "Loan lifecycle",
                "body": "Digitize applications through repayment for MFIs, SACCOs, and cooperatives evaluating CoreTrust.",
                "scope": "external",
            },
            {
                "title": "Savings & collections",
                "body": "Coordinate savings, collections, and operational reporting inside the CoreTrust product.",
                "scope": "external",
            },
            {
                "title": "Compliance posture (honest)",
                "body": "Treat CoreTrust as the system of record for MFI operations. Zreta publishes platform security and billing controls; product-specific regulatory certifications are owned by the CoreTrust deployment.",
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
