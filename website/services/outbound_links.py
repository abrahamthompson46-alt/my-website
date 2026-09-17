"""Build outbound product URLs for homepage trial/demo CTAs."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.db.models import Q
from django.urls import reverse

from products.models import Product, ProductStatus


def build_intent_url(product, intent: str, *, source: str = "homepage") -> str:
    """
    Return a product-site URL for trial or demo, with tracking params.

    intent: "trial" | "demo"
    """
    if intent == "trial":
        base = product.register_url or product.external_app_url or product.demo_url
        campaign = "start_trial"
    else:
        base = product.demo_url or product.external_app_url or product.register_url
        campaign = "request_demo"

    base = (base or "").strip()
    if not base:
        return ""

    parts = urlsplit(base)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update(
        {
            "utm_source": "zreta",
            "utm_medium": source,
            "utm_campaign": campaign,
            "intent": intent,
            "product": product.slug,
        }
    )
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )


def build_tracked_intent_path(product, intent: str, *, source: str = "homepage") -> str:
    """Storefront path that logs the click then redirects to the product site."""
    destination = build_intent_url(product, intent, source=source)
    if not destination:
        return ""
    path = reverse(
        "website:outbound_intent",
        kwargs={"slug": product.slug, "intent": intent},
    )
    return f"{path}?{urlencode({'src': source})}"


def get_homepage_intent_products():
    """Published live storefront products that can receive trial or demo traffic."""
    from products.services.live_products import LIVE_PRODUCT_SLUGS

    return list(
        Product.objects.filter(
            is_published=True,
            status__in=[ProductStatus.GA, ProductStatus.BETA],
            slug__in=LIVE_PRODUCT_SLUGS,
        )
        .filter(
            Q(register_url__gt="")
            | Q(demo_url__gt="")
            | Q(external_app_url__gt="")
        )
        .order_by("sort_order", "name")
    )


def annotate_intent_links(products, *, source: str = "homepage") -> list[dict]:
    """Attach trial_url / demo_url for template rendering (tracked storefront paths)."""
    rows = []
    for product in products:
        # CoreTrust is demo-led — do not attach a self-serve trial CTA.
        if product.slug == "microfinance-core":
            trial_url = ""
        else:
            trial_url = build_tracked_intent_path(product, "trial", source=source)
        demo_url = build_tracked_intent_path(product, "demo", source=source)
        if not trial_url and not demo_url:
            continue
        rows.append(
            {
                "product": product,
                "trial_url": trial_url,
                "demo_url": demo_url,
            }
        )
    return rows
