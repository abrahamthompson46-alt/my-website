from django.db import models

from core.models import BaseModel


class ScreenshotKind(models.TextChoices):
    SCREENSHOT = "screenshot", "Screenshot"
    TEMPLATE = "template", "Template preview"


class ProductScreenshot(BaseModel):
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="screenshots",
    )
    title = models.CharField(max_length=200, blank=True)
    alt_text = models.CharField(max_length=255)
    image = models.ImageField(upload_to="products/screenshots/")
    caption = models.CharField(max_length=255, blank=True)
    kind = models.CharField(
        max_length=20,
        choices=ScreenshotKind.choices,
        default=ScreenshotKind.SCREENSHOT,
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title or self.alt_text


class VideoType(models.TextChoices):
    YOUTUBE = "youtube", "YouTube"
    VIMEO = "vimeo", "Vimeo"
    EXTERNAL = "external", "External URL"
    EMBED = "embed", "Embed Code"


class ProductVideo(BaseModel):
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="videos",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_type = models.CharField(max_length=20, choices=VideoType.choices, default=VideoType.YOUTUBE)
    video_url = models.URLField(blank=True)
    embed_code = models.TextField(blank=True, help_text="Optional raw embed HTML.")
    thumbnail = models.ImageField(upload_to="products/video-thumbs/", blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title


class DownloadType(models.TextChoices):
    BROCHURE = "brochure", "Brochure"
    DATASHEET = "datasheet", "Datasheet"
    WHITEPAPER = "whitepaper", "Whitepaper"
    CASE_STUDY = "case_study", "Case Study"
    OTHER = "other", "Other"


class ProductDownload(BaseModel):
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="downloads",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="products/downloads/")
    file_type = models.CharField(max_length=20, choices=DownloadType.choices, default=DownloadType.BROCHURE)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title
