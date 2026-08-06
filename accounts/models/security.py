from django.db import models
from django.utils import timezone

from core.models import BaseModel


class MFAMethod(models.TextChoices):
    NONE = "none", "None"
    TOTP = "totp", "Authenticator App"
    SMS = "sms", "SMS"
    WEBAUTHN = "webauthn", "Security Key"


class UserSecurityProfile(BaseModel):
    """Security settings and MFA-ready fields for each user."""

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="security_profile",
    )
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    mfa_enabled = models.BooleanField(default=False)
    mfa_method = models.CharField(
        max_length=20,
        choices=MFAMethod.choices,
        default=MFAMethod.NONE,
    )
    mfa_secret = models.CharField(max_length=255, blank=True)
    backup_codes = models.JSONField(default=list, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    must_reset_password = models.BooleanField(default=False)

    class Meta:
        verbose_name = "user security profile"
        verbose_name_plural = "user security profiles"

    def __str__(self):
        return f"Security profile for {self.user.email}"

    @property
    def is_locked(self):
        return bool(self.locked_until and self.locked_until > timezone.now())

    def mark_email_verified(self):
        self.email_verified = True
        self.email_verified_at = timezone.now()
        self.save(update_fields=["email_verified", "email_verified_at", "updated_at"])


class EmailVerificationToken(BaseModel):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )
    token_hash = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_valid(self):
        return self.used_at is None and self.expires_at > timezone.now()


class UserSession(BaseModel):
    """Tracked login session for enterprise session management."""

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="tracked_sessions",
    )
    session_key = models.CharField(max_length=64, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_label = models.CharField(max_length=120, blank=True)
    last_seen_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-last_seen_at"]

    def __str__(self):
        return f"{self.user.email} session {self.session_key[:8]}"

    @property
    def is_active(self):
        return self.revoked_at is None
