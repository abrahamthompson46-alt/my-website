"""Website marketing services."""

from website.services.homepage import (
    HOMEPAGE_FEATURED_LIMIT,
    get_homepage_featured_products,
    get_trust_signals,
    should_show_home_news,
    should_show_home_testimonials,
)

__all__ = [
    "HOMEPAGE_FEATURED_LIMIT",
    "get_homepage_featured_products",
    "get_trust_signals",
    "should_show_home_news",
    "should_show_home_testimonials",
]
