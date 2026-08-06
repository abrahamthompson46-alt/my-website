from django.db import models

from core.models import BaseModel
from payments.constants import GATEWAY_CHOICES


class GatewayConfiguration(BaseModel):
    """Registered payment gateway with non-secret settings."""

    code = models.CharField(max_length=30, choices=GATEWAY_CHOICES, unique=True)
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    supports_recurring = models.BooleanField(default=False)
    supports_refunds = models.BooleanField(default=True)
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Non-secret config: public keys, merchant IDs, allowed manual methods.",
    )

    class Meta:
        ordering = ["-is_default", "name"]
        verbose_name = "gateway configuration"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_default:
            GatewayConfiguration.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
