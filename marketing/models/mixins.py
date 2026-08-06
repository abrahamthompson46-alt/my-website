from django.db import models


class SEOMixin(models.Model):
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    og_image = models.ImageField(upload_to="marketing/og/", blank=True)

    class Meta:
        abstract = True

    @property
    def display_meta_title(self):
        return self.meta_title or getattr(self, "title", "")
