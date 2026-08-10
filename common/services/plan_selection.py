"""Resolve pricing plan selections from URLs and sessions."""

from dataclasses import dataclass

from django.shortcuts import get_object_or_404

from products.models import PricingPlan, PricingTier, Product


@dataclass
class PlanSelection:
    product: Product
    plan: PricingPlan
    tier: PricingTier | None
    action: str  # trial | buy

    @property
    def amount(self):
        if self.tier and self.tier.amount is not None:
            return self.tier.amount
        return None

    @property
    def currency(self):
        if self.tier:
            return self.tier.currency
        return "USD"


def resolve_tier(plan: PricingPlan, tier_id=None, currency=None):
    tiers = plan.tiers.all()
    if tier_id:
        return tiers.filter(pk=tier_id).first()
    if currency:
        match = tiers.filter(currency__iexact=currency).first()
        if match:
            return match
    return tiers.first()


def get_plan_selection(*, product_slug, plan_slug, action="trial", tier_id=None, currency=None):
    product = get_object_or_404(Product, slug=product_slug, is_published=True)
    plan = get_object_or_404(
        PricingPlan,
        product=product,
        slug=plan_slug,
        is_published=True,
    )
    if plan.is_contact_sales:
        raise ValueError("This plan requires contacting sales.")
    tier = resolve_tier(plan, tier_id=tier_id, currency=currency)
    if action not in {"trial", "buy"}:
        raise ValueError("Invalid action.")
    if action == "buy" and (not tier or tier.amount is None):
        raise ValueError("No purchasable price tier configured for this plan.")
    return PlanSelection(product=product, plan=plan, tier=tier, action=action)


def selection_to_session(selection: PlanSelection) -> dict:
    return {
        "product_id": str(selection.product.pk),
        "plan_id": str(selection.plan.pk),
        "tier_id": str(selection.tier.pk) if selection.tier else "",
        "action": selection.action,
    }


def selection_from_session(data: dict) -> PlanSelection | None:
    if not data:
        return None
    try:
        product = Product.objects.get(pk=data["product_id"], is_published=True)
        plan = PricingPlan.objects.get(pk=data["plan_id"], product=product, is_published=True)
        tier = None
        if data.get("tier_id"):
            tier = PricingTier.objects.filter(pk=data["tier_id"], plan=plan).first()
        if not tier:
            tier = plan.tiers.first()
        action = data.get("action", "trial")
        return PlanSelection(product=product, plan=plan, tier=tier, action=action)
    except (Product.DoesNotExist, PricingPlan.DoesNotExist, KeyError):
        return None
