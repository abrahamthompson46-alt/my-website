from django.db import models

from core.models import BaseModel


class DownloadFileType(models.TextChoices):
    PDF = "pdf", "PDF"
    ZIP = "zip", "ZIP Archive"
    SDK = "sdk", "SDK"
    SAMPLE = "sample", "Sample Code"
    OTHER = "other", "Other"


class DocDownload(BaseModel):
    category = models.ForeignKey(
        "documentation.DocCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="downloads",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doc_downloads",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="documentation/downloads/")
    file_type = models.CharField(
        max_length=20,
        choices=DownloadFileType.choices,
        default=DownloadFileType.PDF,
    )
    version = models.CharField(max_length=40, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title
