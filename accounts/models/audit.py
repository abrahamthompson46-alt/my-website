from django.db import models

from core.models import BaseModel


class AuditEventType(models.TextChoices):
    LOGIN_SUCCESS = "login_success", "Login Success"
    LOGIN_FAILED = "login_failed", "Login Failed"
    LOGOUT = "logout", "Logout"
    PASSWORD_CHANGED = "password_changed", "Password Changed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested", "Password Reset Requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed", "Password Reset Completed"
    EMAIL_VERIFIED = "email_verified", "Email Verified"
    EMAIL_VERIFICATION_SENT = "email_verification_sent", "Email Verification Sent"
    MFA_ENABLED = "mfa_enabled", "MFA Enabled"
    MFA_DISABLED = "mfa_disabled", "MFA Disabled"
    MFA_CHALLENGE = "mfa_challenge", "MFA Challenge"
    SESSION_REVOKED = "session_revoked", "Session Revoked"
    ACCOUNT_LOCKED = "account_locked", "Account Locked"
    ACCOUNT_UNLOCKED = "account_unlocked", "Account Unlocked"
    PERMISSION_DENIED = "permission_denied", "Permission Denied"
    ROLE_ASSIGNED = "role_assigned", "Role Assigned"
    ROLE_REMOVED = "role_removed", "Role Removed"
    DEMO_REQUEST_SUBMITTED = "demo_request_submitted", "Demo Request Submitted"
    DEMO_REQUEST_UPDATED = "demo_request_updated", "Demo Request Updated"
    PRODUCT_CREATED = "product_created", "Product Created"
    PRODUCT_UPDATED = "product_updated", "Product Updated"


class AuditLog(BaseModel):
    """Immutable security and authentication audit trail."""

    event_type = models.CharField(max_length=40, choices=AuditEventType.choices)
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    actor = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="performed_audit_logs",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=255, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    message = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} @ {self.created_at:%Y-%m-%d %H:%M}"
