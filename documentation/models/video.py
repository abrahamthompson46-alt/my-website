from django.db import models

from core.models import BaseModel


class DocVideo(BaseModel):
    category = models.ForeignKey(
        "documentation.DocCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="videos",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doc_videos",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    embed_code = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title

    @property
    def duration_display(self):
        if not self.duration_minutes:
            return ""
        return f"{self.duration_minutes} min"
