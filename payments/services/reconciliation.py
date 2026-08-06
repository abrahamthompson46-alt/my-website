from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from payments.models import Payment, PaymentStatus, ReconciliationEntry, ReconciliationRun, ReconciliationStatus


@transaction.atomic
def run_reconciliation(gateway_config, period_start, period_end, run_by=None, gateway_records=None):
    """
    Reconcile internal payments against gateway-provided records.

    gateway_records: list of dicts with keys gateway_reference, amount
    """
    gateway_records = gateway_records or []

    internal_payments = Payment.objects.filter(
        gateway=gateway_config,
        status=PaymentStatus.SUCCEEDED,
        paid_at__date__gte=period_start,
        paid_at__date__lte=period_end,
    )

    internal_total = internal_payments.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    gateway_total = sum(Decimal(str(r.get("amount", 0))) for r in gateway_records)

    run = ReconciliationRun.objects.create(
        gateway=gateway_config,
        period_start=period_start,
        period_end=period_end,
        gateway_total=gateway_total,
        internal_total=internal_total,
        discrepancy_amount=abs(gateway_total - internal_total),
        run_by=run_by,
    )

    internal_by_ref = {p.gateway_reference: p for p in internal_payments if p.gateway_reference}
    matched_refs = set()
    matched_count = 0

    for record in gateway_records:
        ref = record.get("gateway_reference", "")
        gw_amount = Decimal(str(record.get("amount", 0)))
        payment = internal_by_ref.get(ref)
        internal_amount = payment.amount if payment else None
        is_matched = payment is not None and internal_amount == gw_amount
        discrepancy = (internal_amount - gw_amount) if internal_amount is not None else -gw_amount

        ReconciliationEntry.objects.create(
            run=run,
            payment=payment,
            gateway_reference=ref,
            internal_reference=payment.reference if payment else "",
            gateway_amount=gw_amount,
            internal_amount=internal_amount,
            is_matched=is_matched,
            discrepancy=discrepancy,
        )
        if is_matched:
            matched_count += 1
            matched_refs.add(ref)

    unmatched_internal = internal_payments.exclude(gateway_reference__in=matched_refs)
    unmatched_count = unmatched_internal.count()
    for payment in unmatched_internal:
        ReconciliationEntry.objects.create(
            run=run,
            payment=payment,
            gateway_reference=payment.gateway_reference,
            internal_reference=payment.reference,
            internal_amount=payment.amount,
            is_matched=False,
            discrepancy=payment.amount,
            notes="Present internally but not in gateway report.",
        )

    run.matched_count = matched_count
    run.unmatched_count = unmatched_count + max(0, len(gateway_records) - matched_count)
    if run.discrepancy_amount == 0 and run.unmatched_count == 0:
        run.status = ReconciliationStatus.MATCHED
    else:
        run.status = ReconciliationStatus.DISCREPANCY
    run.save()
    return run
