from django.db import models

from core.models import BaseModel


class HTTPMethod(models.TextChoices):
    GET = "GET", "GET"
    POST = "POST", "POST"
    PUT = "PUT", "PUT"
    PATCH = "PATCH", "PATCH"
    DELETE = "DELETE", "DELETE"


class DocAPIEndpoint(BaseModel):
    category = models.ForeignKey(
        "documentation.DocCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="api_endpoints",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="api_endpoints",
    )
    name = models.CharField(max_length=200)
    method = models.CharField(max_length=10, choices=HTTPMethod.choices, default=HTTPMethod.GET)
    path = models.CharField(max_length=500, help_text="e.g. /api/v1/users")
    summary = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    request_example = models.TextField(blank=True)
    response_example = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "path"]

    def __str__(self):
        return f"{self.method} {self.path}"
