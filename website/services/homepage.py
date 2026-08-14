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
}


def get_homepage_featured_products(limit: int = HOMEPAGE_FEATURED_LIMIT):
    """Return published, available featured products ordered by catalog sort order."""
    return list(
        Product.objects.filter(
            is_published=True,
            is_featured=True,
            status__in=[ProductStatus.GA, ProductStatus.BETA],
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
    return getattr(item, "slug", "")


def filter_home_news(articles):
    """Drop seeded placeholder articles from homepage news modules."""
    return [article for article in articles if _item_slug(article) not in _PLACEHOLDER_NEWS_SLUGS]


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
