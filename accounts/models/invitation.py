import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import BaseModel


class InvitationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REVOKED = "revoked", "Revoked"
    EXPIRED = "expired", "Expired"


class StaffInvitation(BaseModel):
    """Invite a user to join the platform with a specific role."""

    email = models.EmailField(db_index=True)
    role = models.ForeignKey(
        "accounts.Role",
        on_delete=models.PROTECT,
        related_name="invitations",
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_invitations",
    )
    token_hash = models.CharField(max_length=64, unique=True)
    grant_staff_access = models.BooleanField(
        default=True,
        help_text="Allow access to Control Room / Operations when accepted.",
    )
    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
    )
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_invitations",
    )
    message = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invite {self.email} → {self.role.name} ({self.status})"

    @property
    def is_valid(self):
        return (
            self.status == InvitationStatus.PENDING
            and self.expires_at > timezone.now()
        )

    @classmethod
    def default_expiry(cls):
        return timezone.now() + timedelta(days=7)

    @staticmethod
    def hash_token(raw_token: str) -> str:
        import hashlib

        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @classmethod
    def generate_token(cls):
        return secrets.token_urlsafe(32)
