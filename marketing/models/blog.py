from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from core.models import BaseModel
from marketing.models.mixins import SEOMixin


class BlogCategory(SEOMixin, BaseModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "blog categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("marketing:blog_category", kwargs={"category_slug": self.slug})


class BlogTag(BaseModel):
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("marketing:blog_tag", kwargs={"tag_slug": self.slug})


class BlogPost(SEOMixin, BaseModel):
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=320, unique=True)
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    author = models.ForeignKey(
        "marketing.Author",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    author_name = models.CharField(max_length=120, blank=True, help_text="Fallback if no author profile.")
    tags = models.ManyToManyField(BlogTag, blank=True, related_name="posts")
    excerpt = models.TextField(blank=True)
    body = models.TextField()
    featured_image = models.ImageField(upload_to="marketing/blog/", blank=True)
    read_time_minutes = models.PositiveIntegerField(default=5)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:300]
        else:
            self.slug = slugify(self.slug)[:300]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("marketing:blog_detail", kwargs={"slug": self.slug})

    @property
    def read_time_display(self):
        return f"{self.read_time_minutes} min read"

    @property
    def display_author(self):
        if self.author:
            return self.author.full_name
        return self.author_name or "Editorial Team"
