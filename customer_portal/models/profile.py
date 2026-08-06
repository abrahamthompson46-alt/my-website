from django.db import models

from core.models import BaseModel


class CustomerProfile(BaseModel):
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    company = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    country = models.CharField(max_length=80, blank=True)
    avatar = models.ImageField(upload_to="portal/avatars/", blank=True)
    email_notifications = models.BooleanField(default=True)
    product_updates = models.BooleanField(default=True)
    billing_alerts = models.BooleanField(default=True)

    class Meta:
        verbose_name = "customer profile"
        verbose_name_plural = "customer profiles"

    def __str__(self):
        return f"Profile — {self.user.email}"
