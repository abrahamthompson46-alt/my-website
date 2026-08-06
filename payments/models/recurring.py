from django.db import models

from core.models import BaseModel


class RecurringStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    CANCELLED = "cancelled", "Cancelled"
    PAST_DUE = "past_due", "Past Due"
    EXPIRED = "expired", "Expired"


class RecurringPayment(BaseModel):
    """Gateway-managed recurring billing agreement."""

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="recurring_payments",
    )
    gateway = models.ForeignKey(
        "payments.GatewayConfiguration",
        on_delete=models.PROTECT,
        related_name="recurring_payments",
    )
    reference = models.CharField(max_length=64, unique=True)
    gateway_subscription_id = models.CharField(max_length=128, blank=True)
    portal_subscription = models.ForeignKey(
        "customer_portal.Subscription",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recurring_payments",
    )
    pricing_plan = models.ForeignKey(
        "products.PricingPlan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recurring_payments",
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    interval = models.CharField(max_length=20, default="monthly")
    status = models.CharField(
        max_length=20,
        choices=RecurringStatus.choices,
        default=RecurringStatus.ACTIVE,
    )
    next_charge_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} ({self.interval})"
