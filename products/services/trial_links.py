"""Helpers for product trial entry points."""

from django.urls import reverse

from products.services.availability import is_purchasable


def get_product_trial_url(product):
    """Return the self-serve trial URL, or empty string when not purchasable."""
    if not is_purchasable(product):
        return ""

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
