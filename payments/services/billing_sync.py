from datetime import timedelta

from django.utils import timezone

from customer_portal.models import Invoice, License, Subscription
from customer_portal.models.invoice import InvoiceStatus
from customer_portal.models.license import LicenseStatus
from customer_portal.models.subscription import BillingInterval, SubscriptionStatus
from products.models.pricing import BillingInterval as PlanBillingInterval

import secrets


def _generate_license_key() -> str:
    return f"ZRT-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"


def _renewal_date(start, billing_interval: str):
    if billing_interval in {BillingInterval.ANNUAL, PlanBillingInterval.ANNUAL}:
        return start + timedelta(days=365)
    return start + timedelta(days=30)


def sync_payment_success(payment):
    """Update portal billing records after successful payment."""
    if payment.invoice_id:
        invoice = payment.invoice
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = timezone.now().date()
        invoice.save(update_fields=["status", "paid_at", "updated_at"])

    recurring_ref = payment.metadata.get("recurring_reference")
    if recurring_ref:
        from payments.models import RecurringPayment

        RecurringPayment.objects.filter(reference=recurring_ref).update(status="active")

    if payment.pricing_plan_id and not payment.invoice_id:
        _ensure_subscription(payment)


def sync_payment_failure(payment):
    if payment.invoice_id:
        invoice = payment.invoice
        if invoice.status == InvoiceStatus.DRAFT:
            invoice.status = InvoiceStatus.OPEN
            invoice.save(update_fields=["status", "updated_at"])


def sync_refund(payment, refund):
    if payment.invoice_id and payment.status == "refunded":
        invoice = payment.invoice
        invoice.status = InvoiceStatus.VOID
        invoice.save(update_fields=["status", "updated_at"])


def _ensure_subscription(payment):
    plan = payment.pricing_plan
    product = plan.product
    existing = Subscription.objects.filter(
        user=payment.user,
        product=product,
        plan_name=plan.name,
        status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL],
    ).first()

    today = timezone.now().date()
    renews = _renewal_date(today, plan.billing_interval)
    billing_interval = (
        BillingInterval.ANNUAL
        if plan.billing_interval == PlanBillingInterval.ANNUAL
        else BillingInterval.MONTHLY
    )

    if existing:
        existing.status = SubscriptionStatus.ACTIVE
        existing.pricing_plan = plan
        existing.amount = payment.amount
        existing.currency = payment.currency
        existing.billing_interval = billing_interval
        existing.trial_ends_at = None
        existing.renews_at = renews
        existing.save(
            update_fields=[
                "status",
                "pricing_plan",
                "amount",
                "currency",
                "billing_interval",
                "trial_ends_at",
                "renews_at",
                "updated_at",
            ]
        )
        subscription = existing
    else:
        subscription = Subscription.objects.create(
            user=payment.user,
            product=product,
            pricing_plan=plan,
            plan_name=plan.name,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=billing_interval,
            amount=payment.amount,
            currency=payment.currency,
            started_at=today,
            renews_at=renews,
        )

    license_obj = License.objects.filter(user=payment.user, product=product, subscription=subscription).first()
    if not license_obj:
        License.objects.create(
            user=payment.user,
            product=product,
            subscription=subscription,
            license_key=_generate_license_key(),
            status=LicenseStatus.ACTIVE,
            seats=1,
            activated_at=today,
            expires_at=renews,
        )
    else:
        license_obj.status = LicenseStatus.ACTIVE
        license_obj.expires_at = renews
        license_obj.save(update_fields=["status", "expires_at", "updated_at"])

    return subscription
