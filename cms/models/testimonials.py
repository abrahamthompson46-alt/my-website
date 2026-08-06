from django.db import models

from core.models import BaseModel


class Testimonial(BaseModel):
    quote = models.TextField()
    author_name = models.CharField(max_length=120)
    author_role = models.CharField(max_length=120, blank=True)
    company = models.CharField(max_length=200, blank=True)
    avatar = models.ImageField(upload_to="cms/testimonials/", blank=True)
    initials = models.CharField(max_length=4, blank=True, help_text="Auto-generated if blank")
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    show_on_home = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="testimonials",
    )

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return f"{self.author_name} — {self.company or 'Testimonial'}"

    def save(self, *args, **kwargs):
        if not self.initials and self.author_name:
            parts = self.author_name.split()
            self.initials = "".join(p[0].upper() for p in parts[:2])
        super().save(*args, **kwargs)
