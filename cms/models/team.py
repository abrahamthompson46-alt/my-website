from django.db import models

from core.models import BaseModel


class TeamMember(BaseModel):
    full_name = models.CharField(max_length=120)
    role = models.CharField(max_length=200)
    department = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="cms/team/", blank=True)
    email = models.EmailField(blank=True)
    linkedin_url = models.URLField(blank=True)
    is_leadership = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    show_on_about = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "full_name"]

    def __str__(self):
        return self.full_name
