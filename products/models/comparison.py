from django.db import models
from django.utils.text import slugify

from core.models import BaseModel


class ComparisonValueType(models.TextChoices):
    BOOLEAN = "boolean", "Yes / No"
    TEXT = "text", "Text"


class ComparisonAttribute(BaseModel):
    """Row in the product comparison matrix."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    group = models.CharField(max_length=120, blank=True, help_text="Section heading in comparison table.")
    value_type = models.CharField(
        max_length=20,
        choices=ComparisonValueType.choices,
        default=ComparisonValueType.BOOLEAN,
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["group", "sort_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductComparisonEntry(BaseModel):
    """Cell value for a product in the comparison matrix."""

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="comparison_entries",
    )
    attribute = models.ForeignKey(
        ComparisonAttribute,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    value_boolean = models.BooleanField(null=True, blank=True)
    value_text = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = [("product", "attribute")]

    def __str__(self):
        return f"{self.product.name} — {self.attribute.name}"

    @property
    def display_value(self):
        if self.attribute.value_type == ComparisonValueType.BOOLEAN:
            if self.value_boolean is True:
                return "yes"
            if self.value_boolean is False:
                return "no"
            return "—"
        return self.value_text or "—"
