"""Add annual plans, GHS tiers, and enable self-serve registration."""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from control_room.models import PlatformSettings
from products.models import PricingPlan, PricingTier, Product
from products.models.pricing import BillingInterval


class Command(BaseCommand):
    help = "Enhance pricing with annual plans, GHS tiers, and buyer-journey defaults."

    @transaction.atomic
    def handle(self, *args, **options):
        ps = PlatformSettings.load()
        ps.public_registration_enabled = True
        ps.save(update_fields=["public_registration_enabled", "updated_at"])
        self.stdout.write("Enabled public self-serve registration.")

        churchhub = Product.objects.filter(slug="churchhub").first()
        if churchhub:
            for monthly in PricingPlan.objects.filter(product=churchhub, billing_interval=BillingInterval.MONTHLY):
                if monthly.is_contact_sales:
                    continue
                annual_slug = f"{monthly.slug}-annual"
                annual, created = PricingPlan.objects.get_or_create(
                    product=churchhub,
                    slug=annual_slug,
                    defaults={
                        "name": f"{monthly.name} (Annual)",
                        "description": monthly.description,
                        "billing_interval": BillingInterval.ANNUAL,
                        "is_popular": monthly.is_popular,
                        "sort_order": monthly.sort_order + 10,
                        "is_published": True,
                    },
                )
                tier = monthly.tiers.filter(currency="USD").first()
                if tier and tier.amount and not annual.tiers.exists():
                    discounted = (tier.amount * Decimal("12") * Decimal("0.8")).quantize(Decimal("0.01"))
                    PricingTier.objects.create(
                        plan=annual,
                        currency="USD",
                        region="global",
                        amount=discounted,
                    )
                    self.stdout.write(f"  Annual plan: {annual.name} @ USD {discounted}")
                if created:
                    for pf in monthly.plan_features.all():
                        annual.plan_features.create(text=pf.text, is_included=pf.is_included, sort_order=pf.sort_order)

            starter = PricingPlan.objects.filter(product=churchhub, slug="starter").first()
            if starter and not starter.tiers.filter(currency="GHS").exists():
                usd = starter.tiers.filter(currency="USD").first()
                if usd and usd.amount:
                    PricingTier.objects.create(
                        plan=starter,
                        currency="GHS",
                        region="africa",
                        amount=(usd.amount * Decimal("15")).quantize(Decimal("0.01")),
                    )
                    self.stdout.write("  Added GHS tier for ChurchHub Starter")

        self.stdout.write(self.style.SUCCESS("Pricing enhancements applied."))
