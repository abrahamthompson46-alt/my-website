from django.conf import settings as django_settings
from django.db import models

from control_room.validators import validate_brand_file_extension, validate_brand_file_size

from core.models import BaseModel


class PlatformSettings(BaseModel):
    """Singleton platform configuration — drives branding, SEO, and global behavior."""

    singleton_key = models.CharField(max_length=32, unique=True, default="default", editable=False)
    site_name = models.CharField(max_length=120, default="Zreta")
    site_tagline = models.CharField(max_length=255, blank=True, default="Modular enterprise software for growing organizations")
    site_description = models.TextField(blank=True, default="Modular enterprise software platform for faith, finance, education, healthcare, and operations.")
    default_seo_title = models.CharField(max_length=120, blank=True, default="Zreta")
    seo_twitter_handle = models.CharField(max_length=80, blank=True)
    seo_default_og_image = models.CharField(max_length=255, blank=True, default="/static/images/og-default.svg")
    contact_email = models.EmailField(blank=True, default="contact@example.com")
    support_email = models.EmailField(blank=True, default="support@example.com")
    contact_phone = models.CharField(max_length=40, blank=True)
    footer_copyright = models.CharField(max_length=255, blank=True, default="© Zreta. All rights reserved.")
    header_cta_primary_label = models.CharField(max_length=60, blank=True, default="Start Free Trial")
    header_cta_primary_url_name = models.CharField(max_length=120, blank=True, default="contact:trial")
    header_cta_secondary_label = models.CharField(max_length=60, blank=True, default="Request a Demo")
    header_cta_secondary_url_name = models.CharField(max_length=120, blank=True, default="contact:demo")
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(
        blank=True,
        default="We are performing scheduled maintenance. Please check back shortly.",
    )
    demo_form_enabled = models.BooleanField(default=True)
    newsletter_enabled = models.BooleanField(default=True)
    partner_program_enabled = models.BooleanField(default=True)
    public_registration_enabled = models.BooleanField(
        default=True,
        help_text="Allow self-serve signup and free trials from pricing pages.",
    )
    social_linkedin_url = models.URLField(blank=True, default="")
    social_twitter_url = models.URLField(blank=True, default="")
    social_youtube_url = models.URLField(blank=True, default="")
    support_sla_hours = models.PositiveIntegerField(
        default=24,
        help_text="Target first-response time in business hours for support tickets.",
    )
    brand_theme_preset = models.CharField(
        max_length=32,
        default="zreta_indigo",
        help_text="Site color theme preset.",
    )
    brand_primary_color = models.CharField(
        max_length=7,
        default="#1e3a5f",
        help_text="Primary brand color (hex), e.g. #1e3a5f",
    )
    brand_accent_color = models.CharField(
        max_length=7,
        default="#c9a227",
        help_text="Accent brand color (hex), e.g. #c9a227",
    )
    brand_logo = models.FileField(
        upload_to="brand/",
        blank=True,
        null=True,
        validators=[validate_brand_file_extension, validate_brand_file_size],
        help_text="Platform logo shown in header and portals (PNG, JPG, WEBP, or SVG; max 2MB).",
    )
    brand_favicon = models.FileField(
        upload_to="brand/",
        blank=True,
        null=True,
        validators=[validate_brand_file_extension, validate_brand_file_size],
        help_text="Optional favicon override (PNG, ICO, or SVG; 32×32 or 64×64 recommended).",
    )

    class Meta:
        verbose_name = "Platform settings"
        verbose_name_plural = "Platform settings"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.singleton_key = "default"
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(
            singleton_key="default",
            defaults={
                "site_name": django_settings.SITE_NAME,
                "site_description": getattr(django_settings, "SITE_DESCRIPTION", ""),
                "default_seo_title": getattr(django_settings, "SITE_DEFAULT_TITLE", django_settings.SITE_NAME),
                "seo_twitter_handle": getattr(django_settings, "SEO_TWITTER_HANDLE", ""),
                "seo_default_og_image": getattr(django_settings, "SEO_DEFAULT_OG_IMAGE", "/static/images/og-default.svg"),
            },
        )
        return obj


class NavigationMenu(BaseModel):
    """Database-driven navigation tree per surface (header, footer, portals)."""

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    structure = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class RedirectRule(BaseModel):
    class RedirectType(models.TextChoices):
        PERMANENT = "301", "Permanent (301)"
        TEMPORARY = "302", "Temporary (302)"

    from_path = models.CharField(max_length=255, unique=True, help_text="Path starting with /, e.g. /old-page/")
    to_path = models.CharField(max_length=255, blank=True, help_text="Absolute path, e.g. /new-page/")
    to_url_name = models.CharField(max_length=120, blank=True, help_text="Django URL name (optional if to_path set)")
    redirect_type = models.CharField(max_length=3, choices=RedirectType.choices, default=RedirectType.PERMANENT)
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["from_path"]

    def __str__(self):
        return f"{self.from_path} → {self.to_path or self.to_url_name}"


class SiteAnnouncement(BaseModel):
    class Variant(models.TextChoices):
        INFO = "info", "Info"
        SUCCESS = "success", "Success"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"

    title = models.CharField(max_length=120)
    message = models.TextField()
    variant = models.CharField(max_length=20, choices=Variant.choices, default=Variant.INFO)
    link_url = models.URLField(blank=True)
    link_label = models.CharField(max_length=60, blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    show_on_public = models.BooleanField(default=True)
    show_on_portal = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.title


class FeatureFlag(BaseModel):
    key = models.SlugField(max_length=80, unique=True)
    label = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_enabled = models.BooleanField(default=False)

    class Meta:
        ordering = ["label"]

    def __str__(self):
        return self.label


class ControlChangeLog(BaseModel):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="control_changes",
    )
    area = models.CharField(max_length=80)
    action = models.CharField(max_length=40)
    summary = models.CharField(max_length=255)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.summary


class PlatformOperationsSettings(BaseModel):
    """Singleton email and deploy settings — platform owner only."""

    singleton_key = models.CharField(max_length=32, unique=True, default="default", editable=False)
    use_custom_smtp = models.BooleanField(
        default=False,
        help_text="When enabled, Control Room SMTP settings override environment email config.",
    )
    smtp_host = models.CharField(max_length=255, blank=True)
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_use_tls = models.BooleanField(default=True)
    smtp_username = models.CharField(max_length=255, blank=True)
    smtp_password = models.CharField(max_length=255, blank=True)
    default_from_email = models.EmailField(blank=True)
    last_email_test_at = models.DateTimeField(null=True, blank=True)
    last_email_test_status = models.CharField(max_length=32, blank=True)
    last_email_test_message = models.TextField(blank=True)
    git_remote = models.CharField(max_length=120, default="origin")
    git_branch = models.CharField(max_length=120, default="main")
    last_deploy_at = models.DateTimeField(null=True, blank=True)
    last_deploy_status = models.CharField(max_length=32, blank=True)
    last_deploy_output = models.TextField(blank=True)
    last_deploy_commit = models.CharField(max_length=64, blank=True)

    class Meta:
        verbose_name = "Platform operations settings"
        verbose_name_plural = "Platform operations settings"
        permissions = [
            ("manage_platform_operations", "Can manage platform email and deploy settings"),
        ]

    def __str__(self):
        return "Platform operations"

    def save(self, *args, **kwargs):
        self.singleton_key = "default"
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(singleton_key="default")
        return obj
