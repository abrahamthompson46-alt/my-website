from django.db import models

from core.models import BaseModel
from core.media_paths import PRIVATE_MEDIA_PREFIX


def private_portal_download_upload_to(instance, filename: str) -> str:
    safe_name = filename.rsplit("/", 1)[-1]
    return f"{PRIVATE_MEDIA_PREFIX}portal/downloads/{safe_name}"


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
    file = models.FileField(upload_to=private_portal_download_upload_to)
    category = models.CharField(
        max_length=20,
        choices=DownloadCategory.choices,
        default=DownloadCategory.INSTALLER,
    )
    version = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="portal_downloads",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "is_active"]),
        ]
    def __str__(self):
        return self.title
