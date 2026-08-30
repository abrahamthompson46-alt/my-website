"""Helpers for product trial entry points."""

from django.urls import reverse


def get_product_trial_url(product):
    """Return the self-serve trial URL for a product's default published plan."""
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
