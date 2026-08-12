"""Platform email delivery with Control Room SMTP overrides."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection

from common.services.email_branding import (
    format_branded_sender,
    get_deliverability_warnings,
    get_email_brand_context,
    get_reply_to_email,
)


class EmailConfigurationError(Exception):
    """Raised when outbound email is not configured correctly."""


def _normalized_from_email(value: str | None) -> str:
    candidate = (value or "").strip()
    if candidate:
        return candidate
    return (getattr(settings, "DEFAULT_FROM_EMAIL", "") or "").strip()


def _validate_backend_settings(backend: str) -> None:
    if backend.endswith("filebased.EmailBackend"):
        file_path = getattr(settings, "EMAIL_FILE_PATH", None)
        if not file_path:
            raise EmailConfigurationError(
                "EMAIL_FILE_PATH is not set for the file-based email backend. "
                "Configure SMTP under Control Room → Platform Ops, or set EMAIL_HOST and "
                "DEFAULT_FROM_EMAIL in your server .env file."
            )


def get_platform_email_settings():
    from control_room.models import PlatformOperationsSettings

    ops = PlatformOperationsSettings.load()
    env_backend = getattr(settings, "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
    env_from = _normalized_from_email(getattr(settings, "DEFAULT_FROM_EMAIL", ""))

    if ops.use_custom_smtp and ops.smtp_host.strip():
        return {
            "backend": "django.core.mail.backends.smtp.EmailBackend",
            "host": ops.smtp_host.strip(),
            "port": ops.smtp_port or 587,
            "username": ops.smtp_username.strip(),
            "password": ops.smtp_password,
            "use_tls": ops.smtp_use_tls,
            "from_email": _normalized_from_email(ops.default_from_email) or env_from,
            "source": "control_room",
        }

    return {
        "backend": env_backend,
        "host": getattr(settings, "EMAIL_HOST", ""),
        "port": getattr(settings, "EMAIL_PORT", 587),
        "username": getattr(settings, "EMAIL_HOST_USER", ""),
        "password": getattr(settings, "EMAIL_HOST_PASSWORD", ""),
        "use_tls": getattr(settings, "EMAIL_USE_TLS", True),
        "from_email": env_from,
        "source": "environment",
    }


def get_platform_mail_connection():
    config = get_platform_email_settings()
    backend = config["backend"]
    _validate_backend_settings(backend)

    if backend.endswith("smtp.EmailBackend"):
        if not config["host"]:
            raise EmailConfigurationError(
                "SMTP host is not configured. Open Control Room → Platform Ops to set email, "
                "or configure EMAIL_HOST in your server .env file."
            )
        return get_connection(
            backend=backend,
            host=config["host"],
            port=config["port"],
            username=config["username"] or None,
            password=config["password"] or None,
            use_tls=config["use_tls"],
            fail_silently=False,
        )

    if backend.endswith("console.EmailBackend") or backend.endswith("locmem.EmailBackend"):
        return get_connection(backend=backend, fail_silently=False)

    if backend.endswith("filebased.EmailBackend"):
        return get_connection(
            backend=backend,
            file_path=settings.EMAIL_FILE_PATH,
            fail_silently=False,
        )

    return get_connection(backend=backend, fail_silently=False)


def send_platform_mail(
    *,
    subject: str,
    message: str,
    recipient_list: list[str],
    from_email: str | None = None,
    from_name: str | None = None,
    html_message: str | None = None,
    reply_to: list[str] | None = None,
    headers: dict[str, str] | None = None,
    fail_silently: bool = False,
):
    config = get_platform_email_settings()
    brand = get_email_brand_context()
    sender = _normalized_from_email(from_email) or config["from_email"]
    if not sender:
        raise EmailConfigurationError(
            "DEFAULT_FROM_EMAIL is not configured. Set it in Platform Ops or your server .env file."
        )

    sender = format_branded_sender(sender, from_name or brand["from_name"])
    reply_addresses = [addr.strip() for addr in (reply_to or []) if addr and "@" in addr]
    if not reply_addresses:
        fallback_reply = get_reply_to_email()
        if fallback_reply:
            reply_addresses = [fallback_reply]

    connection = get_platform_mail_connection()
    mail = EmailMultiAlternatives(
        subject=subject.strip(),
        body=message,
        from_email=sender,
        to=recipient_list,
        connection=connection,
        reply_to=reply_addresses or None,
        headers={
            "X-Entity-Ref-ID": uuid.uuid4().hex,
            "X-Auto-Response-Suppress": "All",
            **(headers or {}),
        },
    )
    if html_message:
        mail.attach_alternative(html_message, "text/html")
    return mail.send(fail_silently=fail_silently)


def get_email_status_summary() -> dict:
    config = get_platform_email_settings()
    issues: list[str] = []

    if not config["from_email"]:
        issues.append("Missing DEFAULT_FROM_EMAIL")

    backend = config["backend"]
    if backend.endswith("smtp.EmailBackend") and not config["host"]:
        issues.append("Missing SMTP host")
    if backend.endswith("filebased.EmailBackend") and not getattr(settings, "EMAIL_FILE_PATH", None):
        issues.append("EMAIL_FILE_PATH is not set for file-based email backend")

    return {
        "configured": not issues,
        "source": config["source"],
        "backend": backend.rsplit(".", 1)[-1],
        "from_email": config["from_email"] or "—",
        "host": config["host"] or "—",
        "issues": issues,
        "deliverability_warnings": get_deliverability_warnings(config["from_email"]),
    }
