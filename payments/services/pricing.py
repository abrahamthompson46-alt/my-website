"""Server-side checkout pricing — client amounts are never authoritative."""

from __future__ import annotations

from decimal import Decimal

from common.money import MONEY_QUANT, quantize_money
from customer_portal.models import Invoice
from customer_portal.models.invoice import InvoiceStatus
from products.models import PricingPlan, PricingTier, Product, ProductStatus


class CheckoutPricingError(ValueError):
    """Raised when checkout identifiers or client price hints are invalid."""


def _reject_client_price_hints(
    *,
    posted_amount: str | Decimal | None,
    posted_currency: str | None,
    authoritative_amount: Decimal,
    authoritative_currency: str,
) -> None:
    """Reject requests that attempt to supply a different price than the server calculated."""
    if posted_amount not in (None, ""):
        try:
            client_amount = quantize_money(Decimal(str(posted_amount)))
        except Exception as exc:
            raise CheckoutPricingError("Invalid payment amount.") from exc
        if client_amount != authoritative_amount:
            raise CheckoutPricingError("Payment amount does not match the selected plan or invoice.")

    if posted_currency:
        client_currency = posted_currency.strip().upper()[:3]
        if client_currency != authoritative_currency.upper():
            raise CheckoutPricingError("Payment currency does not match the selected plan or invoice.")


def _resolve_invoice_pricing(*, user, invoice_id) -> dict:
    if not invoice_id:
        return None
    try:
        invoice = Invoice.objects.get(pk=invoice_id, user=user)
    except Invoice.DoesNotExist as exc:
        raise CheckoutPricingError("Invoice not found.") from exc

    if invoice.status not in {InvoiceStatus.OPEN, InvoiceStatus.OVERDUE}:
        raise CheckoutPricingError("This invoice cannot be paid.")

    amount = quantize_money(invoice.amount)
    if amount <= ZERO:
        raise CheckoutPricingError("Invoice amount must be greater than zero.")

    return {
        "amount": amount,
        "currency": invoice.currency.upper()[:3],
        "invoice": invoice,
        "pricing_plan": None,
        "pricing_tier": None,
    }


def _resolve_plan_pricing(*, plan_id, tier_id) -> dict:
    if not plan_id:
        return None

    try:
        plan = PricingPlan.objects.select_related("product").get(pk=plan_id)
    except PricingPlan.DoesNotExist as exc:
        raise CheckoutPricingError("Pricing plan not found.") from exc

    if not plan.is_published or plan.is_contact_sales:
        raise CheckoutPricingError("Selected plan is not available for purchase.")

    product = plan.product
    if not product.is_published or product.status not in {ProductStatus.GA, ProductStatus.BETA}:
        raise CheckoutPricingError("Selected product is not available for purchase.")

    if tier_id:
        try:
            tier = PricingTier.objects.get(pk=tier_id, plan=plan)
        except PricingTier.DoesNotExist as exc:
            raise CheckoutPricingError("Pricing tier not found for the selected plan.") from exc
    else:
        tier = plan.tiers.order_by("region", "currency").first()
        if not tier:
            raise CheckoutPricingError("Selected plan has no purchasable price.")

    if tier.amount is None:
        raise CheckoutPricingError("Selected plan has no purchasable price.")

    amount = quantize_money(tier.amount)
    if amount <= ZERO:
        raise CheckoutPricingError("Plan price must be greater than zero.")

    return {
        "amount": amount,
        "currency": tier.currency.upper()[:3],
        "invoice": None,
        "pricing_plan": plan,
        "pricing_tier": tier,
    }


ZERO = Decimal("0")


def resolve_checkout_pricing(
    *,
    user,
    invoice_id=None,
    plan_id=None,
    tier_id=None,
    posted_amount=None,
    posted_currency=None,
) -> dict:
    """
    Calculate authoritative checkout amount/currency from trusted server records.

    Accepts plan/invoice identifiers only. Optional posted_amount/currency are
    validated and rejected when they do not match the server calculation.
    """
    invoice_id = (invoice_id or "").strip() or None
    plan_id = (plan_id or "").strip() or None
    tier_id = (tier_id or "").strip() or None

    if invoice_id and plan_id:
        raise CheckoutPricingError("Provide either an invoice or a plan, not both.")

    if not invoice_id and not plan_id:
        raise CheckoutPricingError("Select a plan or invoice to pay.")

    if invoice_id:
        result = _resolve_invoice_pricing(user=user, invoice_id=invoice_id)
    else:
        result = _resolve_plan_pricing(plan_id=plan_id, tier_id=tier_id)

    _reject_client_price_hints(
        posted_amount=posted_amount,
        posted_currency=posted_currency,
        authoritative_amount=result["amount"],
        authoritative_currency=result["currency"],
    )
    return result


def assert_payment_matches_sources(
    *,
    amount: Decimal,
    currency: str,
    invoice=None,
    pricing_tier=None,
) -> None:
    """Defense-in-depth validation inside payment creation."""
    normalized_amount = quantize_money(amount)
    normalized_currency = currency.upper()[:3]

    if invoice is not None:
        if quantize_money(invoice.amount) != normalized_amount:
            raise CheckoutPricingError("Payment amount does not match invoice.")
        if invoice.currency.upper()[:3] != normalized_currency:
            raise CheckoutPricingError("Payment currency does not match invoice.")
        return

    if pricing_tier is not None:
        if pricing_tier.amount is None:
            raise CheckoutPricingError("Pricing tier has no amount.")
        if quantize_money(pricing_tier.amount) != normalized_amount:
            raise CheckoutPricingError("Payment amount does not match pricing tier.")
        if pricing_tier.currency.upper()[:3] != normalized_currency:
            raise CheckoutPricingError("Payment currency does not match pricing tier.")
        return

    raise CheckoutPricingError("Payment must be linked to an invoice or pricing tier.")
