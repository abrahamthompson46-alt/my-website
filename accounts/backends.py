from django.conf import settings
from datetime import timedelta

from django.contrib.auth.backends import ModelBackend
from django.utils import timezone

from accounts.models import AuditEventType
from accounts.services.audit import log_audit_event
from accounts.services.email import get_or_create_security_profile


class EnterpriseAuthBackend(ModelBackend):
    """Authentication backend with account lockout enforcement."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username=username, password=password, **kwargs)
        if user is None:
            return None

        profile = get_or_create_security_profile(user)
        if profile.is_locked:
            log_audit_event(
                AuditEventType.LOGIN_FAILED,
                request=request,
                user=user,
                message="Account locked",
            )
            return None
        return user

    def user_can_authenticate(self, user):
        if not super().user_can_authenticate(user):
            return False
        profile = get_or_create_security_profile(user)
        return not profile.is_locked


def record_failed_login(request, email):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        return

    profile = get_or_create_security_profile(user)
    profile.failed_login_attempts += 1
    max_attempts = getattr(settings, "AUTH_MAX_LOGIN_ATTEMPTS", 5)
    lock_minutes = getattr(settings, "AUTH_LOCKOUT_MINUTES", 30)
    if profile.failed_login_attempts >= max_attempts:
        profile.locked_until = timezone.now() + timedelta(minutes=lock_minutes)
        profile.save(update_fields=["failed_login_attempts", "locked_until", "updated_at"])
        log_audit_event(
            AuditEventType.ACCOUNT_LOCKED,
            request=request,
            user=user,
            message=f"Locked after {max_attempts} failed attempts",
        )
    else:
        profile.save(update_fields=["failed_login_attempts", "updated_at"])


def reset_failed_login(user):
    profile = get_or_create_security_profile(user)
    if profile.failed_login_attempts or profile.locked_until:
        profile.failed_login_attempts = 0
        profile.locked_until = None
        profile.save(update_fields=["failed_login_attempts", "locked_until", "updated_at"])
