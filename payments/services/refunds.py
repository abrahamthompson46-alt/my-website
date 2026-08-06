import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from payments.gateways.dto import RefundRequest
from payments.gateways.registry import get_gateway_from_model
from payments.models import PaymentStatus, Refund, RefundStatus
from payments.services.billing_sync import sync_refund


def generate_refund_reference():
    return f"REF-{uuid.uuid4().hex[:16].upper()}"


@transaction.atomic
def create_refund(payment, amount: Decimal, reason="", initiated_by=None):
    if payment.status not in {PaymentStatus.SUCCEEDED, PaymentStatus.PARTIALLY_REFUNDED}:
        raise ValueError("Only successful payments can be refunded.")
    if amount <= 0 or amount > payment.refundable_amount:
        raise ValueError("Invalid refund amount.")

    reference = generate_refund_reference()
    refund = Refund.objects.create(
        payment=payment,
        reference=reference,
        amount=amount,
        currency=payment.currency,
        reason=reason,
        initiated_by=initiated_by,
        status=RefundStatus.PENDING,
    )

    adapter = get_gateway_from_model(payment.gateway)
    request = RefundRequest(
        payment_reference=payment.reference,
        gateway_reference=payment.gateway_reference,
        amount=amount,
        currency=payment.currency,
        reason=reason,
    )
    result = adapter.create_refund(request)

    refund.gateway_refund_id = result.gateway_reference
    if result.success:
        refund.status = RefundStatus.SUCCEEDED
        refund.processed_at = timezone.now()
    else:
        refund.status = RefundStatus.FAILED
    refund.metadata = result.raw_response
    refund.save()

    if result.success:
        _update_payment_refund_status(payment)
        sync_refund(payment, refund)

    return refund, result


def _update_payment_refund_status(payment):
    total_refunded = sum(
        r.amount for r in payment.refunds.filter(status=RefundStatus.SUCCEEDED)
    )
    if total_refunded >= payment.amount:
        payment.status = PaymentStatus.REFUNDED
    elif total_refunded > 0:
        payment.status = PaymentStatus.PARTIALLY_REFUNDED
    payment.save(update_fields=["status", "updated_at"])
