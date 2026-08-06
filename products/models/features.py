from django.db import models
from django.utils.text import slugify

from core.models import BaseModel


class ProductModule(BaseModel):
    """Functional module grouping within a product."""

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="modules",
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        unique_together = [("product", "slug")]

    def __str__(self):
        return f"{self.product.name} — {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductFeature(BaseModel):
    """Feature bullet or capability for a product."""

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="features",
    )
    module = models.ForeignKey(
        ProductModule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="features",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_highlighted = models.BooleanField(default=False)
    plans = models.ManyToManyField(
        "products.PricingPlan",
        blank=True,
        related_name="features",
        help_text="Plans that include this feature. Empty = all plans.",
    )

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title
