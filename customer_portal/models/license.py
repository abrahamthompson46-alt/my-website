from django.db import models

from core.models import BaseModel


class LicenseStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    EXPIRED = "expired", "Expired"
    REVOKED = "revoked", "Revoked"


class License(BaseModel):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="licenses",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="licenses",
    )
    subscription = models.ForeignKey(
        "customer_portal.Subscription",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="licenses",
    )
    license_key = models.CharField(max_length=64, unique=True)
    status = models.CharField(
        max_length=20,
        choices=LicenseStatus.choices,
        default=LicenseStatus.ACTIVE,
    )
    seats = models.PositiveIntegerField(default=1)
    activated_at = models.DateField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name} — {self.license_key[:8]}…"
