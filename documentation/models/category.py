from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from core.models import BaseModel


class DocCategory(BaseModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=80, blank=True, default="folder")
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doc_categories",
    )

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "documentation category"
        verbose_name_plural = "documentation categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("documentation:category", kwargs={"slug": self.slug})
