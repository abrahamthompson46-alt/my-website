from django.db import models

from core.models import BaseModel


class ProductContentSection(BaseModel):
    """Additional CMS-managed sections displayed on product detail pages."""

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="cms_sections",
    )
    title = models.CharField(max_length=255)
    subtitle = models.TextField(blank=True)
    body = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return f"{self.product.name} — {self.title}"
