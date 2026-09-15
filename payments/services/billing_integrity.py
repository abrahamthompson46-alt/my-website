"""Billing relationship integrity helpers."""

from __future__ import annotations


class BillingIntegrityError(ValueError):
    """Raised when linked billing records disagree on user/org/product."""


def assert_linked_user(*, user, related, label: str) -> None:
    if related is None:
        return
    related_user_id = getattr(related, "user_id", None)
    if related_user_id and user and related_user_id != getattr(user, "pk", user):
        raise BillingIntegrityError(
            f"{label} user does not match the linked record's user."
        )


def assert_linked_organization(*, organization, related, label: str) -> None:
    if related is None or organization is None:
        return
    related_org_id = getattr(related, "organization_id", None)
    org_id = getattr(organization, "pk", organization)
    if related_org_id and org_id and related_org_id != org_id:
        raise BillingIntegrityError(
            f"{label} organization does not match the linked record's organization."
        )


def assert_subscription_links(*, user, organization, subscription, product=None) -> None:
    if subscription is None:
        return
    assert_linked_user(user=user, related=subscription, label="Subscription")
    assert_linked_organization(
        organization=organization, related=subscription, label="Subscription"
    )
    if product is not None and subscription.product_id and subscription.product_id != product.pk:
        raise BillingIntegrityError("Subscription product does not match expected product.")
