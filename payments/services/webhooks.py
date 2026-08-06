"""Payment webhook processing with validation."""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from common.money import MONEY_QUANT
from payments.gateways.registry import get_gateway_from_model
from payments.models import Payment, PaymentAttempt, PaymentStatus, WebhookEvent
from payments.services.billing_sync import sync_payment_failure, sync_payment_success

_MINOR_UNIT_GATEWAYS = {"paystack", "flutterwave", "hubtel"}
_TERMINAL_SUCCESS = {PaymentStatus.SUCCEEDED, PaymentStatus.REFUNDED}
_TERMINAL_FAILURE = {PaymentStatus.FAILED, PaymentStatus.CANCELLED}


@transaction.atomic
def process_webhook(gateway_config, payload: dict, raw_body: bytes, headers: dict):
    adapter = get_gateway_from_model(gateway_config)
    signature_valid = adapter.verify_webhook(raw_body, headers) if adapter.supports_webhooks else True

    parsed = adapter.parse_webhook(payload, headers)
    event_id = (
        payload.get("id")
        or payload.get("event.id")
        or payload.get("data", {}).get("id")
        or f"{parsed.event_type}:{parsed.reference}:{parsed.gateway_reference}"
    )

    webhook_event, created = WebhookEvent.objects.get_or_create(
        gateway=gateway_config,
        event_id=str(event_id),
        defaults={
            "event_type": parsed.event_type,
            "payload": payload,
            "headers": dict(headers),
            "signature_valid": signature_valid,
        },
    )
    if not created:
        return webhook_event, False

    if not signature_valid:
        webhook_event.error_message = "Invalid webhook signature."
        webhook_event.save(update_fields=["error_message", "updated_at"])
        return webhook_event, False

    if not parsed.handled or not parsed.reference:
        webhook_event.processed = True
        webhook_event.processed_at = timezone.now()
        webhook_event.save(update_fields=["processed", "processed_at", "updated_at"])
        return webhook_event, True

    payment = Payment.objects.filter(reference=parsed.reference).first()
    if not payment and parsed.gateway_reference:
        payment = Payment.objects.filter(gateway_reference=parsed.gateway_reference).first()

    if payment:
        webhook_event.payment = payment
        ok, reason = _validate_webhook_payment(payment, parsed, gateway_config.code)
        if not ok:
            webhook_event.error_message = reason
            webhook_event.save(update_fields=["payment", "error_message", "updated_at"])
            return webhook_event, False

        _apply_webhook_status(payment, parsed.status, parsed.raw_payload)
        webhook_event.processed = True
        webhook_event.processed_at = timezone.now()
        webhook_event.save()
    else:
        webhook_event.error_message = f"Payment not found for reference {parsed.reference}"
        webhook_event.save(update_fields=["error_message", "updated_at"])

    return webhook_event, True


def _normalize_amount(amount, gateway_code: str, expected: Decimal) -> Decimal | None:
    if amount is None:
        return None
    value = Decimal(str(amount))
    if gateway_code in _MINOR_UNIT_GATEWAYS and value > expected * Decimal("10"):
        value = value / Decimal("100")
    return value


def _validate_webhook_payment(payment, parsed, gateway_code: str) -> tuple[bool, str]:
    if payment.status in _TERMINAL_SUCCESS:
        return False, f"Payment already in terminal state: {payment.status}"

    if parsed.gateway_reference and payment.gateway_reference:
        if str(parsed.gateway_reference) != str(payment.gateway_reference):
            return False, "Gateway reference mismatch."

    if parsed.currency and payment.currency:
        if parsed.currency.upper() != payment.currency.upper():
            return False, "Currency mismatch."

    normalized = _normalize_amount(parsed.amount, gateway_code, payment.amount)
    if normalized is not None and abs(normalized - payment.amount) > MONEY_QUANT:
        return False, f"Amount mismatch: expected {payment.amount}, received {normalized}."

    return True, ""


def _apply_webhook_status(payment, status, raw_payload):
    status = (status or "").lower()
    if status in {"succeeded", "success", "successful", "paid"}:
        if payment.status == PaymentStatus.SUCCEEDED:
            return payment
        payment.status = PaymentStatus.SUCCEEDED
        payment.paid_at = timezone.now()
        payment.save()
        PaymentAttempt.objects.create(
            payment=payment,
            gateway_reference=payment.gateway_reference,
            status=PaymentStatus.SUCCEEDED,
            response_data=raw_payload,
        )
        sync_payment_success(payment)
    elif status in {"failed", "failure", "cancelled", "canceled"}:
        if payment.status in _TERMINAL_FAILURE:
            return payment
        payment.status = PaymentStatus.FAILED
        payment.failed_at = timezone.now()
        payment.save()
        PaymentAttempt.objects.create(
            payment=payment,
            gateway_reference=payment.gateway_reference,
            status=PaymentStatus.FAILED,
            response_data=raw_payload,
        )
        sync_payment_failure(payment)
    elif status == "refunded":
        payment.status = PaymentStatus.REFUNDED
        payment.save()
    return payment


@transaction.atomic
def verify_payment(payment):
    adapter = get_gateway_from_model(payment.gateway)
    result = adapter.verify_payment(payment.reference)
    if result.success:
        payment.status = PaymentStatus.SUCCEEDED
        payment.paid_at = timezone.now()
        payment.gateway_reference = result.gateway_reference or payment.gateway_reference
        payment.save()
        PaymentAttempt.objects.create(
            payment=payment,
            gateway_reference=result.gateway_reference,
            status=PaymentStatus.SUCCEEDED,
            response_data=result.raw_response,
        )
        sync_payment_success(payment)
    elif result.status in {"failed", "cancelled"}:
        payment.status = PaymentStatus.FAILED
        payment.failed_at = timezone.now()
        payment.failure_reason = result.message
        payment.save()
        sync_payment_failure(payment)
    return payment, result
