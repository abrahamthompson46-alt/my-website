from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from core.models import BaseModel
from marketing.models.mixins import SEOMixin


class ResourceType(models.TextChoices):
    GUIDE = "guide", "Guide"
    TEMPLATE = "template", "Template"
    CHECKLIST = "checklist", "Checklist"
    EBOOK = "ebook", "E-book"
    TOOLKIT = "toolkit", "Toolkit"
    OTHER = "other", "Other"


class MarketingResource(SEOMixin, BaseModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices, default=ResourceType.GUIDE)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="marketing/resources/", blank=True)
    external_url = models.URLField(blank=True)
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marketing_resources",
    )
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("marketing:resources")
