"""Canonical live storefront products marketed and billed through Zreta."""

from __future__ import annotations

# Products that are live external apps (not roadmap catalog fillers).
LIVE_PRODUCT_SLUGS = frozenset({"churchhub", "microfinance-core"})


def is_live_storefront_product(product) -> bool:
    """True when the product is a verified live Zreta storefront offering."""
    if not product:
        return False
    slug = getattr(product, "slug", "") or ""
    if slug not in LIVE_PRODUCT_SLUGS:
        return False
    if not getattr(product, "is_published", False):
        return False
    status = getattr(product, "status", None)
    from products.models import ProductStatus

    return status in {ProductStatus.GA, ProductStatus.BETA}


def is_external_product(product) -> bool:
    """True when acquisition should continue on the product's own site."""
    return bool(
        product
        and (
            (getattr(product, "external_app_url", "") or "").strip()
            or (getattr(product, "register_url", "") or "").strip()
            or (getattr(product, "demo_url", "") or "").strip()
        )
    )
