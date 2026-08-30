"""Rate limiting for public marketing and checkout forms."""

from accounts.services.rate_limit import check_auth_rate_limit, log_rate_limit_exceeded

CHECKOUT_LIMIT = 15
CHECKOUT_WINDOW = 3600
NEWSLETTER_LIMIT = 10
NEWSLETTER_WINDOW = 3600
CONTACT_LIMIT = 5
CONTACT_WINDOW = 3600
WEBHOOK_LIMIT = 120
WEBHOOK_WINDOW = 3600


def is_checkout_rate_limited(request) -> bool:
    user = getattr(request, "user", None)
    identifier = str(user.pk) if getattr(user, "is_authenticated", False) else ""
    return check_auth_rate_limit(
        request,
        scope="checkout-submit",
        identifier=identifier,
        limit=CHECKOUT_LIMIT,
        window_seconds=CHECKOUT_WINDOW,
    )


def log_checkout_rate_limit(request):
    log_rate_limit_exceeded(request, "checkout-submit")


def is_newsletter_rate_limited(request) -> bool:
    return check_auth_rate_limit(
        request,
        scope="newsletter-submit",
        limit=NEWSLETTER_LIMIT,
        window_seconds=NEWSLETTER_WINDOW,
    )


def log_newsletter_rate_limit(request):
    log_rate_limit_exceeded(request, "newsletter-submit")


def is_contact_rate_limited(request) -> bool:
    return check_auth_rate_limit(
        request,
        scope="contact-submit",
        limit=CONTACT_LIMIT,
        window_seconds=CONTACT_WINDOW,
    )


def log_contact_rate_limit(request):
    log_rate_limit_exceeded(request, "contact-submit")


def is_webhook_rate_limited(request, gateway_code: str) -> bool:
    return check_auth_rate_limit(
        request,
        scope=f"webhook-{gateway_code}",
        limit=WEBHOOK_LIMIT,
        window_seconds=WEBHOOK_WINDOW,
    )


def log_webhook_rate_limit(request, gateway_code: str):
    log_rate_limit_exceeded(request, f"webhook-{gateway_code}")
