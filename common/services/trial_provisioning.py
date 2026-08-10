"""Provision self-serve product trials for new and existing customers."""

import secrets
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from accounts.models import Role
from accounts.services.rbac import assign_role
from customer_portal.models import CustomerProfile, License, Subscription
from customer_portal.models.license import LicenseStatus
from customer_portal.models.subscription import BillingInterval, SubscriptionStatus
from products.models.pricing import BillingInterval as PlanBillingInterval

User = get_user_model()

DEFAULT_TRIAL_DAYS = 14


def _generate_license_key() -> str:
    return f"ZRT-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"


def _renewal_date(start, billing_interval: str):
    if billing_interval == PlanBillingInterval.ANNUAL:
        return start + timedelta(days=365)
    return start + timedelta(days=30)


@transaction.atomic
def provision_trial(
    *,
    user,
    product,
    plan,
    tier=None,
    company="",
    trial_days: int = DEFAULT_TRIAL_DAYS,
):
    """Create or refresh a trial subscription and portal license."""
    today = timezone.now().date()
    trial_end = today + timedelta(days=trial_days)

    existing = Subscription.objects.filter(
        user=user,
        product=product,
        status__in=[SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE],
    ).first()
    if existing:
        if existing.status == SubscriptionStatus.TRIAL:
            existing.trial_ends_at = trial_end
            existing.plan_name = plan.name
            existing.pricing_plan = plan
            existing.save(update_fields=["trial_ends_at", "plan_name", "pricing_plan", "updated_at"])
            return existing
        return existing

    amount = tier.amount if tier and tier.amount is not None else Decimal("0")
    currency = tier.currency if tier else "USD"
    billing_interval = (
        BillingInterval.ANNUAL
        if plan.billing_interval == PlanBillingInterval.ANNUAL
        else BillingInterval.MONTHLY
    )

    subscription = Subscription.objects.create(
        user=user,
        product=product,
        pricing_plan=plan,
        plan_name=plan.name,
        status=SubscriptionStatus.TRIAL,
        billing_interval=billing_interval,
        amount=amount,
        currency=currency,
        started_at=today,
        trial_ends_at=trial_end,
        renews_at=trial_end,
    )

    License.objects.create(
        user=user,
        product=product,
        subscription=subscription,
        license_key=_generate_license_key(),
        status=LicenseStatus.ACTIVE,
        seats=1,
        activated_at=today,
        expires_at=trial_end,
    )

    if company:
        CustomerProfile.objects.update_or_create(
            user=user,
            defaults={"company": company},
        )

    customer_role = Role.objects.filter(slug="customer").first()
    if customer_role:
        assign_role(user, customer_role)

    return subscription


def expire_due_trials():
    """Mark expired trials and suspend linked licenses."""
    today = timezone.now().date()
    expired = Subscription.objects.filter(
        status=SubscriptionStatus.TRIAL,
        trial_ends_at__lt=today,
    )
    count = 0
    for sub in expired.select_related("user", "product"):
        sub.status = SubscriptionStatus.EXPIRED
        sub.save(update_fields=["status", "updated_at"])
        License.objects.filter(subscription=sub, status=LicenseStatus.ACTIVE).update(
            status=LicenseStatus.EXPIRED
        )
        count += 1
    return count
