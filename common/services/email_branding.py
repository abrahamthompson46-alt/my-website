"""Brand context and deliverability helpers for transactional email."""

from __future__ import annotations

from email.utils import formataddr
from urllib.parse import urlparse

from django.conf import settings
from django.utils import timezone

DISPOSABLE_FROM_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "icloud.com",
    "aol.com",
}


def _site_domain() -> str:
    host = urlparse(getattr(settings, "SITE_URL", "") or "").netloc.lower()
    return host[4:] if host.startswith("www.") else host


def _email_domain(address: str) -> str:
    cleaned = (address or "").strip()
    if "<" in cleaned and ">" in cleaned:
        cleaned = cleaned.split("<", 1)[1].split(">", 1)[0]
    if "@" not in cleaned:
        return ""
    return cleaned.rsplit("@", 1)[-1].lower()


def format_branded_sender(from_email: str, from_name: str | None = None) -> str:
    email = (from_email or "").strip()
    if not email:
        return email
    if "<" in email and ">" in email:
        return email
    name = (from_name or "").strip()
    if name:
        return formataddr((name, email))
    return email


def get_reply_to_email() -> str:
    from control_room.services import get_platform_settings

    ps = get_platform_settings()
    for candidate in (ps.support_email, ps.contact_email, getattr(settings, "DEFAULT_FROM_EMAIL", "")):
        if candidate and "@" in candidate:
            return candidate.strip()
    return ""


def get_email_brand_context(extra: dict | None = None) -> dict:
    from control_room.services import get_platform_settings
    from control_room.services.theme import get_brand_colors

    ps = get_platform_settings()
    brand = get_brand_colors(ps)
    site_url = (getattr(settings, "SITE_URL", "") or "").rstrip("/")
    site_name = ps.site_name or getattr(settings, "SITE_NAME", "Platform")

    if ps.brand_logo:
        logo_url = f"{site_url}{ps.brand_logo.url}"
    else:
        logo_url = f"{site_url}/static/images/brand/png/logo-full-420.png"

    context = {
        "site_name": site_name,
        "site_url": site_url,
        "site_tagline": ps.site_tagline or "Classic software for modern enterprise teams",
        "support_email": ps.support_email or ps.contact_email or "",
        "contact_email": ps.contact_email or "",
        "footer_copyright": ps.footer_copyright or f"© {timezone.now().year} {site_name}. All rights reserved.",
        "brand_primary": brand["primary"],
        "brand_accent": brand["accent"],
        "brand_primary_dark": brand.get("theme_color") or brand["primary"],
        "logo_url": logo_url,
        "from_name": site_name,
        "current_year": timezone.now().year,
    }
    if extra:
        context.update(extra)
    return context


def get_deliverability_warnings(from_email: str) -> list[str]:
    warnings: list[str] = []
    sender = (from_email or "").strip()
    if not sender:
        warnings.append("Set a From address that matches your domain (e.g. noreply@yourdomain.com).")
        return warnings

    from_domain = _email_domain(sender)
    site_domain = _site_domain()

    if from_domain in DISPOSABLE_FROM_DOMAINS:
        warnings.append(
            f"From address uses {from_domain}. Use an address on your own domain "
            f"(e.g. noreply@{site_domain or 'yourdomain.com'}) so invitations are less likely to land in spam."
        )
    elif site_domain and from_domain and from_domain != site_domain:
        warnings.append(
            f"From domain ({from_domain}) does not match your site domain ({site_domain}). "
            "Align them and add SPF, DKIM, and DMARC DNS records for best deliverability."
        )

    if site_domain:
        warnings.append(
            f"Add SPF, DKIM, and DMARC records for {site_domain}. "
            "Your email provider's dashboard usually includes the exact DNS values."
        )

    return warnings
