from django.db import models

from core.models import BaseModel


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    TRIAL = "trial", "Trial"
    PAST_DUE = "past_due", "Past Due"
    CANCELLED = "cancelled", "Cancelled"
    EXPIRED = "expired", "Expired"


class BillingInterval(models.TextChoices):
    MONTHLY = "monthly", "Monthly"
    ANNUAL = "annual", "Annual"


class Subscription(BaseModel):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    plan_name = models.CharField(max_length=120)
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
    )
    billing_interval = models.CharField(
        max_length=20,
        choices=BillingInterval.choices,
        default=BillingInterval.ANNUAL,
    )
    seats = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")
    started_at = models.DateField()
    renews_at = models.DateField(null=True, blank=True)
    cancelled_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.user.email} — {self.product.name} ({self.plan_name})"

    @property
    def is_active(self):
        return self.status in {SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL}
