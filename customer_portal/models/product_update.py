from django.db import models

from core.models import BaseModel


class UpdateType(models.TextChoices):
    RELEASE = "release", "Release"
    SECURITY = "security", "Security Patch"
    FEATURE = "feature", "New Feature"
    MAINTENANCE = "maintenance", "Maintenance"


class ProductUpdate(BaseModel):
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="portal_updates",
    )
    title = models.CharField(max_length=255)
    version = models.CharField(max_length=40, blank=True)
    update_type = models.CharField(
        max_length=20,
        choices=UpdateType.choices,
        default=UpdateType.RELEASE,
    )
    summary = models.TextField()
    body = models.TextField(blank=True)
    published_at = models.DateTimeField()
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return f"{self.product.name} {self.version} — {self.title}"
