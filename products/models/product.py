from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from core.models import BaseModel


class ProductStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    COMING_SOON = "coming_soon", "Coming Soon"
    BETA = "beta", "Beta"
    GA = "ga", "Generally Available"
    DEPRECATED = "deprecated", "Deprecated"


class ProductAccent(models.TextChoices):
    CHURCHHUB = "churchhub", "ChurchHub (Indigo)"
    MICROFINANCE = "microfinance", "Microfinance (Teal)"
    ERP = "erp", "ERP (Blue)"
    SCHOOL = "school", "School (Purple)"
    HOSPITAL = "hospital", "Hospital (Cyan)"
    HR = "hr", "HR & Payroll (Orange)"
    DEFAULT = "default", "Default (Primary Blue)"


class Product(BaseModel):
    """Core SaaS product catalog entry."""

    category = models.ForeignKey(
        "products.ProductCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    tagline = models.CharField(max_length=255, blank=True)
    short_description = models.TextField(blank=True)
    long_description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.DRAFT,
    )
    accent = models.CharField(
        max_length=20,
        choices=ProductAccent.choices,
        default=ProductAccent.DEFAULT,
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    launch_date = models.DateField(null=True, blank=True)
    external_app_url = models.URLField(blank=True)
    documentation_url = models.URLField(blank=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    hero_image = models.ImageField(upload_to="products/heroes/", blank=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("products:detail", kwargs={"slug": self.slug})

    @property
    def is_available(self):
        return self.status in {ProductStatus.BETA, ProductStatus.GA}

    @property
    def is_future(self):
        return self.status in {ProductStatus.COMING_SOON, ProductStatus.DRAFT}

    @property
    def display_meta_title(self):
        return self.meta_title or self.name
