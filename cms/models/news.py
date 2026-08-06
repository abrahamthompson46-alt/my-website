from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from core.models import BaseModel


class NewsArticle(BaseModel):
    """Press releases and company news (distinct from blog posts)."""

    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=320, unique=True)
    category = models.CharField(max_length=120, blank=True, default="Company News")
    excerpt = models.TextField(blank=True)
    body = models.TextField(blank=True)
    external_url = models.URLField(blank=True, help_text="Link to external press release if any.")
    featured_image = models.ImageField(upload_to="cms/news/", blank=True)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "news article"
        verbose_name_plural = "news articles"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        if self.external_url:
            return self.external_url
        return reverse("cms:news_detail", kwargs={"slug": self.slug})
