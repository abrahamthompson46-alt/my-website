"""Audit logging for payment lifecycle events."""

from accounts.models import AuditEventType
from accounts.services.audit import log_audit_event


def log_payment_event(
    event_type,
    payment,
    *,
    request=None,
    actor=None,
    message="",
    metadata=None,
):
    base_metadata = {
        "payment_id": str(payment.pk),
        "reference": payment.reference,
        "amount": str(payment.amount),
        "currency": payment.currency,
        "status": payment.status,
    }
    if metadata:
        base_metadata.update(metadata)
    log_audit_event(
        event_type,
        request=request,
        user=payment.user,
        actor=actor,
        message=message or f"Payment {payment.reference}",
        metadata=base_metadata,
    )


def log_payment_created(payment, *, request=None):
    log_payment_event(
        AuditEventType.PAYMENT_CREATED,
        payment,
        request=request,
        message=f"Payment created: {payment.reference}",
    )


def log_payment_succeeded(payment, *, request=None, source=""):
    metadata = {"source": source} if source else None
    log_payment_event(
        AuditEventType.PAYMENT_SUCCEEDED,
        payment,
        request=request,
        message=f"Payment succeeded: {payment.reference}",
        metadata=metadata,
    )


def log_payment_refunded(payment, *, request=None, actor=None, refund_reference="", metadata=None):
    extra = dict(metadata or {})
    if refund_reference:
        extra["refund_reference"] = refund_reference
    log_payment_event(
        AuditEventType.PAYMENT_REFUNDED,
        payment,
        request=request,
        actor=actor,
        message=f"Payment refunded: {payment.reference}",
        metadata=extra or None,
    )


def log_payment_manual_confirmed(payment, *, request=None, actor=None):
    log_payment_event(
        AuditEventType.PAYMENT_MANUAL_CONFIRMED,
        payment,
        request=request,
        actor=actor,
        message=f"Manual payment confirmed: {payment.reference}",
    )
