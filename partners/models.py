from django.db import models

from core.models import BaseModel


class PartnerTier(models.TextChoices):
    REGISTERED = "registered", "Registered"
    SILVER = "silver", "Silver"
    GOLD = "gold", "Gold"
    PLATINUM = "platinum", "Platinum"


class PartnerProfile(BaseModel):
    """Partner account linked to a platform user."""

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="partner_profile",
    )
    company_name = models.CharField(max_length=200)
    tier = models.CharField(
        max_length=20,
        choices=PartnerTier.choices,
        default=PartnerTier.REGISTERED,
    )
    referral_code = models.CharField(max_length=32, unique=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    is_active = models.BooleanField(default=True)
    website = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["company_name"]

    def __str__(self):
        return self.company_name
