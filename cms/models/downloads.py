from django.db import models

from core.models import BaseModel


class DownloadCategory(models.TextChoices):
    BROCHURE = "brochure", "Brochure"
    WHITEPAPER = "whitepaper", "Whitepaper"
    DATASHEET = "datasheet", "Datasheet"
    CASE_STUDY = "case_study", "Case Study"
    MEDIA_KIT = "media_kit", "Media Kit"
    OTHER = "other", "Other"


class CMSDownload(BaseModel):
    """Site-wide downloadable resources managed in CMS."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="cms/downloads/")
    category = models.CharField(max_length=20, choices=DownloadCategory.choices, default=DownloadCategory.BROCHURE)
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cms_downloads",
    )
    is_published = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title
