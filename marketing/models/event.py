from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from core.models import BaseModel
from marketing.models.mixins import SEOMixin


class EventType(models.TextChoices):
    WEBINAR = "webinar", "Webinar"
    CONFERENCE = "conference", "Conference"
    WORKSHOP = "workshop", "Workshop"
    MEETUP = "meetup", "Meetup"
    VIRTUAL = "virtual", "Virtual Event"


class MarketingEvent(SEOMixin, BaseModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    event_type = models.CharField(max_length=20, choices=EventType.choices, default=EventType.WEBINAR)
    excerpt = models.TextField(blank=True)
    body = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    virtual_url = models.URLField(blank=True)
    registration_url = models.URLField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    featured_image = models.ImageField(upload_to="marketing/events/", blank=True)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["starts_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("marketing:event_detail", kwargs={"slug": self.slug})

    @property
    def is_upcoming(self):
        from django.utils import timezone

        return self.starts_at >= timezone.now()
