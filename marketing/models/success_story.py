from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from core.models import BaseModel
from marketing.models.mixins import SEOMixin


class SuccessStory(SEOMixin, BaseModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    company = models.CharField(max_length=200)
    industry = models.CharField(max_length=120, blank=True)
    quote = models.TextField(blank=True)
    excerpt = models.TextField(blank=True)
    body = models.TextField(blank=True)
    result_metric = models.CharField(max_length=120, blank=True, help_text="e.g. 35% increase in efficiency")
    featured_image = models.ImageField(upload_to="marketing/success-stories/", blank=True)
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="success_stories",
    )
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "-created_at"]
        verbose_name_plural = "success stories"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("marketing:success_story_detail", kwargs={"slug": self.slug})
