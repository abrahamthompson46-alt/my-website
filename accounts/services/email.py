import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from accounts.models import EmailVerificationToken, UserSecurityProfile


def get_or_create_security_profile(user):
    profile, _ = UserSecurityProfile.objects.get_or_create(user=user)
    return profile


def _hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_email_verification_token(user, hours_valid=24):
    token = secrets.token_urlsafe(32)
    EmailVerificationToken.objects.filter(user=user, used_at__isnull=True).update(
        used_at=timezone.now()
    )
    return EmailVerificationToken.objects.create(
        user=user,
        token_hash=_hash_token(token),
        expires_at=timezone.now() + timedelta(hours=hours_valid),
    ), token


def verify_email_token(token):
    token_hash = _hash_token(token)
    record = (
        EmailVerificationToken.objects.select_related("user")
        .filter(token_hash=token_hash, used_at__isnull=True, expires_at__gt=timezone.now())
        .first()
    )
    if not record:
        return None
    record.used_at = timezone.now()
    record.save(update_fields=["used_at", "updated_at"])
    profile = get_or_create_security_profile(record.user)
    profile.mark_email_verified()
    return record.user


def send_verification_email(request, user):
    token_record, raw_token = create_email_verification_token(user)
    verify_url = request.build_absolute_uri(
        reverse("accounts:verify_email", kwargs={"token": raw_token})
    )
    context = {
        "user": user,
        "verify_url": verify_url,
        "site_name": settings.SITE_NAME,
        "expires_hours": 24,
    }
    subject = render_to_string("accounts/email/verify_email_subject.txt", context).strip()
    text_body = render_to_string("accounts/email/verify_email_body.txt", context)
    html_body = render_to_string("accounts/email/verify_email_body.html", context)
    send_mail(
        subject,
        text_body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_body,
        fail_silently=False,
    )
    return token_record


def parse_user_agent(user_agent):
    ua = (user_agent or "").lower()
    if "mobile" in ua or "iphone" in ua or "android" in ua:
        device = "Mobile"
    elif "tablet" in ua or "ipad" in ua:
        device = "Tablet"
    else:
        device = "Desktop"
    if "chrome" in ua:
        browser = "Chrome"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "safari" in ua:
        browser = "Safari"
    elif "edge" in ua:
        browser = "Edge"
    else:
        browser = "Browser"
    return f"{browser} on {device}"
