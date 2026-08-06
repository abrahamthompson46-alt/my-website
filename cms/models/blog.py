from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from core.models import BaseModel


class BlogCategory(BaseModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "blog categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BlogPost(BaseModel):
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=320, unique=True)
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    author_name = models.CharField(max_length=120, blank=True)
    excerpt = models.TextField(blank=True)
    body = models.TextField()
    featured_image = models.ImageField(upload_to="cms/blog/", blank=True)
    read_time_minutes = models.PositiveIntegerField(default=5)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("marketing:blog_detail", kwargs={"slug": self.slug})

    @property
    def read_time_display(self):
        return f"{self.read_time_minutes} min read"

    @property
    def display_meta_title(self):
        return self.meta_title or self.title
