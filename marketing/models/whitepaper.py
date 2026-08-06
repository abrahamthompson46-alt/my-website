from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from core.models import BaseModel
from marketing.models.mixins import SEOMixin


class WhitePaper(SEOMixin, BaseModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    excerpt = models.TextField(blank=True)
    body = models.TextField(blank=True)
    file = models.FileField(upload_to="marketing/whitepapers/", blank=True)
    cover_image = models.ImageField(upload_to="marketing/whitepapers/covers/", blank=True)
    is_gated = models.BooleanField(default=True, help_text="Require email before download.")
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="whitepapers",
    )
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("marketing:whitepaper_detail", kwargs={"slug": self.slug})
