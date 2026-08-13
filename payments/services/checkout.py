import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from payments.gateways.dto import PaymentInitRequest, RecurringRequest
from payments.gateways.registry import get_gateway_from_model
from payments.services.pricing import CheckoutPricingError, assert_payment_matches_sources
from payments.models import (
    GatewayConfiguration,
    ManualPaymentDetail,
    ManualPaymentMethod,
    Payment,
    PaymentAttempt,
    PaymentStatus,
    PaymentType,
    RecurringPayment,
    RecurringStatus,
)

VALID_RECURRING_INTERVALS = frozenset({"daily", "weekly", "monthly", "yearly"})


def generate_reference(prefix="PAY"):
    return f"{prefix}-{uuid.uuid4().hex[:16].upper()}"


def get_default_gateway():
    return GatewayConfiguration.objects.filter(is_active=True, is_default=True).first()


def resolve_gateway(gateway_code=None):
    if gateway_code:
        return GatewayConfiguration.objects.filter(code=gateway_code, is_active=True).first()
    return get_default_gateway()


@transaction.atomic
def create_checkout(
    *,
    user,
    amount: Decimal,
    currency: str,
    gateway_code=None,
    description="",
    customer_email="",
    callback_url="",
    invoice=None,
    pricing_plan=None,
    pricing_tier=None,
    metadata=None,
    idempotency_key="",
    manual_method="",
    manual_detail=None,
):
    gateway_config = resolve_gateway(gateway_code)
    if not gateway_config:
        raise ValueError("No active payment gateway configured.")

    assert_payment_matches_sources(
        amount=amount,
        currency=currency,
        invoice=invoice,
        pricing_tier=pricing_tier,
    )

    reference = generate_reference()
    idempotency_key = idempotency_key or reference
    payment_type = PaymentType.MANUAL if manual_method else PaymentType.ONE_TIME

    payment = Payment.objects.create(
        user=user,
        gateway=gateway_config,
        reference=reference,
        idempotency_key=idempotency_key,
        amount=amount,
        currency=currency,
        status=PaymentStatus.PENDING,
        payment_type=payment_type,
        manual_method=manual_method or "",
        description=description,
        customer_email=customer_email or user.email,
        callback_url=callback_url,
        invoice=invoice,
        pricing_plan=pricing_plan,
        pricing_tier=pricing_tier,
        metadata=metadata or {},
    )

    if manual_method and manual_detail:
        ManualPaymentDetail.objects.create(payment=payment, **manual_detail)

    adapter = get_gateway_from_model(gateway_config)
    init_request = PaymentInitRequest(
        reference=reference,
        amount=amount,
        currency=currency,
        email=payment.customer_email,
        callback_url=callback_url,
        metadata={
            **(metadata or {}),
            "manual_method": manual_method,
            "description": description,
            "customer_name": user.display_name,
        },
        idempotency_key=idempotency_key,
    )
    result = adapter.initialize_payment(init_request)

    payment.gateway_reference = result.gateway_reference
    payment.authorization_url = result.authorization_url
    if manual_method:
        payment.status = PaymentStatus.PENDING_CONFIRMATION
    elif result.authorization_url:
        payment.status = PaymentStatus.PROCESSING
    payment.save()

    PaymentAttempt.objects.create(
        payment=payment,
        gateway_reference=result.gateway_reference,
        status=payment.status,
        response_data=result.raw_response,
        error_message="" if result.success else result.message,
    )
    return payment, result


@transaction.atomic
def create_recurring_checkout(
    *,
    user,
    amount: Decimal,
    currency: str,
    interval: str,
    gateway_code=None,
    pricing_plan=None,
    portal_subscription=None,
    metadata=None,
    callback_url="",
):
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    if interval not in VALID_RECURRING_INTERVALS:
        raise ValueError(f"Invalid billing interval: {interval}")

    gateway_config = resolve_gateway(gateway_code)
    if not gateway_config or not gateway_config.supports_recurring:
        raise ValueError("No recurring-capable gateway configured.")

    reference = generate_reference("SUB")
    recurring = RecurringPayment.objects.create(
        user=user,
        gateway=gateway_config,
        reference=reference,
        portal_subscription=portal_subscription,
        pricing_plan=pricing_plan,
        amount=amount,
        currency=currency,
        interval=interval,
        metadata=metadata or {},
    )

    adapter = get_gateway_from_model(gateway_config)
    request = RecurringRequest(
        reference=reference,
        amount=amount,
        currency=currency,
        email=user.email,
        interval=interval,
        callback_url=callback_url,
        metadata={**(metadata or {}), "plan_name": pricing_plan.name if pricing_plan else "Subscription"},
    )
    result = adapter.create_recurring(request)
    recurring.gateway_subscription_id = result.gateway_reference or ""

    if not result.success:
        recurring.status = RecurringStatus.CANCELLED
        recurring.cancelled_at = timezone.now()
        recurring.save(update_fields=["gateway_subscription_id", "status", "cancelled_at", "updated_at"])
        raise ValueError(result.message or "Recurring setup failed at the gateway.")

    recurring.next_charge_at = timezone.now()
    recurring.save(update_fields=["gateway_subscription_id", "next_charge_at", "updated_at"])

    payment, _ = create_checkout(
        user=user,
        amount=amount,
        currency=currency,
        gateway_code=gateway_config.code,
        description=f"Recurring setup: {reference}",
        customer_email=user.email,
        callback_url=callback_url,
        pricing_plan=pricing_plan,
        metadata={"recurring_reference": reference, **(metadata or {})},
        idempotency_key=reference,
    )
    payment.payment_type = PaymentType.RECURRING
    payment.save(update_fields=["payment_type", "updated_at"])
    return recurring, payment, result


@transaction.atomic
def confirm_manual_payment(payment, confirmed_by, notes=""):
    if payment.status != PaymentStatus.PENDING_CONFIRMATION:
        raise ValueError("Payment is not awaiting manual confirmation.")

    from payments.constants import MANUAL
    from payments.gateways.manual import ManualGateway
    from payments.services.billing_sync import sync_payment_success

    adapter = ManualGateway(payment.gateway.settings)
    result = adapter.confirm_payment(payment.reference, confirmed_by=confirmed_by.email)

    payment.status = PaymentStatus.SUCCEEDED
    payment.paid_at = timezone.now()
    payment.gateway_reference = result.gateway_reference
    payment.save()

    detail = getattr(payment, "manual_detail", None)
    if detail:
        detail.confirmed_by = confirmed_by
        detail.confirmed_at = timezone.now()
        if notes:
            detail.notes = notes
        detail.save()

    PaymentAttempt.objects.create(
        payment=payment,
        gateway_reference=result.gateway_reference,
        status=PaymentStatus.SUCCEEDED,
        response_data=result.raw_response,
    )
    sync_payment_success(payment)
    return payment
