"""Helpers for product trial entry points."""

from django.urls import reverse

from products.services.availability import is_purchasable
from products.services.live_products import is_external_product


def get_product_trial_url(product, *, source: str = "product_page"):
    """
    Return the best trial/start URL for a product.

    External live products continue via a tracked Zreta redirect to their register/demo URL.
    In-platform products use Zreta plan-start checkout.
    """
    if not is_purchasable(product):
        return ""

    if is_external_product(product):
        from website.services.outbound_links import build_tracked_intent_path

        return build_tracked_intent_path(product, "trial", source=source)

    plan = (
        product.plans.filter(is_published=True, is_contact_sales=False)
        .order_by("sort_order", "name")
        .first()
    )
    if not plan:
        return reverse("products:pricing", kwargs={"slug": product.slug})
    return (
        reverse("products:plan_start", kwargs={"slug": product.slug})
        + f"?plan={plan.slug}&action=trial"
    )


def get_product_demo_url(product, *, source: str = "product_page"):
    """Return a tracked outbound demo path when the product hosts its own demo intake."""
    if not is_external_product(product):
        return ""
    from website.services.outbound_links import build_tracked_intent_path

    return build_tracked_intent_path(product, "demo", source=source)
