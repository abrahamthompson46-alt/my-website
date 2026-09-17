"""Homepage presentation rules — Zreta platform with multiple product lines."""

from __future__ import annotations

from products.models import Product, ProductStatus

HOMEPAGE_FEATURED_LIMIT = 3

# Slugs seeded as illustrative until replaced with verified customer stories.
_PLACEHOLDER_TESTIMONIAL_AUTHORS = {
    "Sarah Okonkwo",
    "Rev. James Mwangi",
    "Dr. Amina Hassan",
}

# CMS / marketing seed content that should not display on the public homepage.
_PLACEHOLDER_NEWS_SLUGS = {
    "enterprise-platform-expands-18-countries",
    "enterprise-platform-achieves-soc-2-type-ii",
    "introducing-hospital-management-2-0",
}

_BLOCKED_NEWS_TITLE_FRAGMENTS = (
    "hospital management 2.0",
    "soc 2 type ii",
    "expands to 18 countries",
    "trusted by thousands",
)


def get_homepage_featured_products(limit: int = HOMEPAGE_FEATURED_LIMIT):
    """Return published live storefront products for the homepage feature strip."""
    from products.services.live_products import LIVE_PRODUCT_SLUGS

    return list(
        Product.objects.filter(
            is_published=True,
            is_featured=True,
            status__in=[ProductStatus.GA, ProductStatus.BETA],
            slug__in=LIVE_PRODUCT_SLUGS,
        )
        .prefetch_related("features", "plans")
        .order_by("sort_order")[:limit]
    )


def get_trust_signals(fallback: list | None = None) -> list:
    from website.content import TRUST_SIGNALS

    return fallback if fallback else TRUST_SIGNALS


def _item_author_name(item) -> str | None:
    if isinstance(item, dict):
        return item.get("author_name") or item.get("name")
    return getattr(item, "author_name", None)


def _item_slug(item) -> str:
    if isinstance(item, dict):
        return item.get("slug", "")
    return getattr(item, "slug", "") or ""


def _item_title(item) -> str:
    if isinstance(item, dict):
        return (item.get("title") or "").lower()
    return (getattr(item, "title", "") or "").lower()


def filter_home_news(articles):
    """Drop seeded / contradictory articles from homepage news modules."""
    cleaned = []
    for article in articles:
        slug = _item_slug(article)
        title = _item_title(article)
        if slug in _PLACEHOLDER_NEWS_SLUGS:
            continue
        if any(fragment in title for fragment in _BLOCKED_NEWS_TITLE_FRAGMENTS):
            continue
        cleaned.append(article)
    return cleaned


def should_show_home_testimonials(testimonials) -> bool:
    if not testimonials:
        return False
    for item in testimonials:
        name = _item_author_name(item)
        if name and name not in _PLACEHOLDER_TESTIMONIAL_AUTHORS:
            return True
    return False


def should_show_home_news(articles) -> bool:
    articles = filter_home_news(articles)
    return bool(articles)
