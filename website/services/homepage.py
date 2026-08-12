"""Homepage presentation rules — honest, ChurchHub-first, conversion-focused."""

from __future__ import annotations

from products.models import Product, ProductStatus

HOMEPAGE_FEATURED_LIMIT = 3

# Slugs seeded as illustrative until replaced with verified customer stories.
_PLACEHOLDER_TESTIMONIAL_AUTHORS = {
    "Sarah Okonkwo",
    "Rev. James Mwangi",
    "Dr. Amina Hassan",
}

# CMS seed article titles that should not display once sync has run.
_PLACEHOLDER_NEWS_SLUGS = {
    "enterprise-platform-expands-18-countries",
}


def get_homepage_featured_products(limit: int = HOMEPAGE_FEATURED_LIMIT):
    """Return published, available products with ChurchHub pinned first."""
    qs = (
        Product.objects.filter(
            is_published=True,
            is_featured=True,
            status__in=[ProductStatus.GA, ProductStatus.BETA],
        )
        .prefetch_related("features", "plans")
        .order_by("sort_order")
    )
    products = list(qs)
    products.sort(key=lambda product: (0 if product.slug == "churchhub" else 1, product.sort_order))
    return products[:limit]


def get_trust_signals(fallback: list | None = None) -> list:
    from website.content import TRUST_SIGNALS

    return fallback if fallback else TRUST_SIGNALS


def _item_author_name(item) -> str | None:
    if isinstance(item, dict):
        return item.get("author_name") or item.get("name")
    return getattr(item, "author_name", None)


def should_show_home_testimonials(testimonials) -> bool:
    if not testimonials:
        return False
    for item in testimonials:
        name = _item_author_name(item)
        if name and name not in _PLACEHOLDER_TESTIMONIAL_AUTHORS:
            return True
    return False


def should_show_home_news(articles) -> bool:
    if not articles:
        return False
    for article in articles:
        slug = getattr(article, "slug", "")
        if slug in _PLACEHOLDER_NEWS_SLUGS:
            continue
        return True
    return False
