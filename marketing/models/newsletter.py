from django.db import models

from core.models import BaseModel


class NewsletterSubscriber(BaseModel):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=120, blank=True)
    source = models.CharField(max_length=80, blank=True, default="website")
    is_active = models.BooleanField(default=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email
