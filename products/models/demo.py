from django.db import models

from core.models import BaseModel


class DemoRequestStatus(models.TextChoices):
    NEW = "new", "New"
    CONTACTED = "contacted", "Contacted"
    SCHEDULED = "scheduled", "Scheduled"
    COMPLETED = "completed", "Completed"
    CLOSED = "closed", "Closed"


class ProductDemoRequest(BaseModel):
    """Demo request tied to a product."""

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="demo_requests",
    )
    full_name = models.CharField(max_length=120)
    work_email = models.EmailField()
    company = models.CharField(max_length=200)
    phone = models.CharField(max_length=30, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=DemoRequestStatus.choices,
        default=DemoRequestStatus.NEW,
    )
    source = models.CharField(max_length=80, blank=True, default="website")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        product_name = self.product.name if self.product else "General"
        return f"{self.full_name} — {product_name}"
