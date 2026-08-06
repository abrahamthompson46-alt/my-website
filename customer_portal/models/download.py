from django.db import models

from core.models import BaseModel


class DownloadCategory(models.TextChoices):
    INSTALLER = "installer", "Installer"
    DOCUMENTATION = "documentation", "Documentation"
    SDK = "sdk", "SDK"
    TEMPLATE = "template", "Template"
    OTHER = "other", "Other"


class CustomerDownload(BaseModel):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="portal_downloads",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="portal_downloads",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="portal/downloads/")
    category = models.CharField(
        max_length=20,
        choices=DownloadCategory.choices,
        default=DownloadCategory.INSTALLER,
    )
    version = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
