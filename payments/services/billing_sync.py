from django.utils import timezone

from customer_portal.models import Invoice, Subscription
from customer_portal.models.invoice import InvoiceStatus
from customer_portal.models.subscription import SubscriptionStatus


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
    if existing:
        return existing

    today = timezone.now().date()
    return Subscription.objects.create(
        user=payment.user,
        product=product,
        plan_name=plan.name,
        status=SubscriptionStatus.ACTIVE,
        billing_interval=plan.billing_interval,
        amount=payment.amount,
        currency=payment.currency,
        started_at=today,
        renews_at=today,
    )
