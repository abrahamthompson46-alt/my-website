from django.db import models

from core.models import BaseModel


class HeroPlacement(models.TextChoices):
    HOME = "home", "Home Page"
    ABOUT = "about", "About Page"
    PRODUCT = "product", "Product Page"
    BLOG = "blog", "Blog"
    CUSTOM = "custom", "Custom"


class HeroBanner(BaseModel):
    """Reusable hero banner editable from the CMS."""

    name = models.CharField(max_length=200, help_text="Admin label for this hero")
    placement = models.CharField(max_length=20, choices=HeroPlacement.choices, default=HeroPlacement.CUSTOM)
    eyebrow = models.CharField(max_length=120, blank=True)
    headline = models.CharField(max_length=500)
    subheadline = models.TextField(blank=True)
    trust_text = models.CharField(max_length=255, blank=True)
    background_image = models.ImageField(upload_to="cms/heroes/", blank=True)
    cta_primary_label = models.CharField(max_length=120, blank=True)
    cta_primary_url = models.CharField(max_length=500, blank=True)
    cta_secondary_label = models.CharField(max_length=120, blank=True)
    cta_secondary_url = models.CharField(max_length=500, blank=True)
    linked_product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hero_banners",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
