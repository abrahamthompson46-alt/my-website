from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from core.models import BaseModel


class Author(BaseModel):
    full_name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    role = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="marketing/authors/", blank=True)
    email = models.EmailField(blank=True)
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.full_name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("marketing:author_detail", kwargs={"slug": self.slug})
