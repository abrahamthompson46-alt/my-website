from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from core.models import BaseModel


class PageType(models.TextChoices):
    HOME = "home", "Home Page"
    ABOUT = "about", "About Page"
    CUSTOM = "custom", "Custom Page"
    LANDING = "landing", "Landing Page"


class CMSPage(BaseModel):
    """Editable site page managed through the CMS."""

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    page_type = models.CharField(max_length=20, choices=PageType.choices, default=PageType.CUSTOM)
    hero = models.ForeignKey(
        "cms.HeroBanner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pages",
    )
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "CMS page"
        verbose_name_plural = "CMS pages"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        if self.page_type == PageType.HOME:
            return reverse("website:home")
        if self.page_type == PageType.ABOUT:
            return reverse("pages:about")
        return reverse("pages:detail", kwargs={"slug": self.slug})

    @property
    def display_meta_title(self):
        return self.meta_title or self.title


class PageSection(BaseModel):
    """Configurable section on a CMS page (hero area, features grid, CTA, etc.)."""

    page = models.ForeignKey(CMSPage, on_delete=models.CASCADE, related_name="sections")
    section_key = models.SlugField(max_length=80, help_text="Unique key within the page, e.g. why_choose_us")
    title = models.CharField(max_length=255, blank=True)
    subtitle = models.TextField(blank=True)
    eyebrow = models.CharField(max_length=120, blank=True)
    body = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    settings = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["sort_order", "section_key"]
        unique_together = [("page", "section_key")]

    def __str__(self):
        return f"{self.page.slug} — {self.section_key}"


class SectionItem(BaseModel):
    """Repeatable item inside a page section (stat, feature, industry, partner logo, etc.)."""

    section = models.ForeignKey(PageSection, on_delete=models.CASCADE, related_name="items")
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=80, blank=True, help_text="Lucide icon name")
    image = models.ImageField(upload_to="cms/sections/", blank=True)
    link_url = models.CharField(max_length=500, blank=True)
    link_label = models.CharField(max_length=120, blank=True)
    value = models.CharField(max_length=120, blank=True, help_text="For statistics or short values")
    extra_data = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title
