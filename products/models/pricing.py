from django.db import models
from django.utils.text import slugify

from core.models import BaseModel


class BillingInterval(models.TextChoices):
    MONTHLY = "monthly", "Monthly"
    ANNUAL = "annual", "Annual"
    ONE_TIME = "one_time", "One-time"
    CUSTOM = "custom", "Custom / Contact Sales"


class PricingPlan(BaseModel):
    """Pricing plan tier for a product."""

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="plans",
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, blank=True)
    description = models.TextField(blank=True)
    billing_interval = models.CharField(
        max_length=20,
        choices=BillingInterval.choices,
        default=BillingInterval.MONTHLY,
    )
    is_popular = models.BooleanField(default=False)
    is_contact_sales = models.BooleanField(
        default=False,
        help_text="When enabled, price displays as 'Contact Sales' instead of amount.",
    )
    is_published = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        unique_together = [("product", "slug")]

    def __str__(self):
        return f"{self.product.name} — {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PricingTier(BaseModel):
    """Regional / currency-specific price for a plan."""

    plan = models.ForeignKey(
        PricingPlan,
        on_delete=models.CASCADE,
        related_name="tiers",
    )
    region = models.CharField(max_length=10, default="global", help_text="e.g. global, us, eu, africa")
    currency = models.CharField(max_length=3, default="USD")
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_label = models.CharField(
        max_length=80,
        blank=True,
        help_text="Override display, e.g. 'Custom pricing'",
    )

    class Meta:
        ordering = ["region", "currency"]
        unique_together = [("plan", "region", "currency")]

    def __str__(self):
        return f"{self.plan} ({self.currency})"

    @property
    def display_price(self):
        if self.price_label:
            return self.price_label
        if self.plan.is_contact_sales:
            return "Contact Sales"
        if self.amount is not None:
            return f"{self.currency} {self.amount:,.2f}"
        return "Contact Sales"


class PlanFeature(BaseModel):
    """Feature bullet listed on a pricing plan card."""

    plan = models.ForeignKey(
        PricingPlan,
        on_delete=models.CASCADE,
        related_name="plan_features",
    )
    text = models.CharField(max_length=255)
    is_included = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "text"]

    def __str__(self):
        prefix = "✓" if self.is_included else "✗"
        return f"{prefix} {self.text}"
