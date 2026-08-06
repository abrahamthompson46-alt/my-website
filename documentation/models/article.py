from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from core.models import BaseModel
from documentation.constants import ARTICLE_TYPES


class DocArticle(BaseModel):
    category = models.ForeignKey(
        "documentation.DocCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doc_articles",
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    article_type = models.CharField(max_length=30, choices=ARTICLE_TYPES, default="guide")
    excerpt = models.TextField(blank=True)
    body = models.TextField()
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True)
    version = models.CharField(max_length=40, blank=True, help_text="For release notes.")

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:240]
            slug = base
            counter = 1
            while DocArticle.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("documentation:article", kwargs={"slug": self.slug})

    @property
    def display_excerpt(self):
        return self.excerpt or self.body[:200]
