"""Customer onboarding and lifecycle email notifications."""

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse


def _send(template_prefix, subject_context, body_context, recipient):
    subject = render_to_string(f"emails/{template_prefix}_subject.txt", subject_context).strip()
    text_body = render_to_string(f"emails/{template_prefix}_body.txt", body_context)
    html_body = render_to_string(f"emails/{template_prefix}_body.html", body_context)
    send_mail(
        subject,
        text_body,
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
        html_message=html_body,
        fail_silently=False,
    )


def send_trial_welcome_email(request, user, subscription):
    portal_url = request.build_absolute_uri(reverse("customer_portal:dashboard"))
    product_url = subscription.product.external_app_url or portal_url
    context = {
        "user": user,
        "subscription": subscription,
        "product": subscription.product,
        "trial_ends_at": subscription.trial_ends_at,
        "portal_url": portal_url,
        "product_url": product_url,
        "site_name": settings.SITE_NAME,
        "support_email": getattr(settings, "SUPPORT_EMAIL", settings.DEFAULT_FROM_EMAIL),
    }
    _send("trial_welcome", context, context, user.email)


def send_trial_expiring_email(user, subscription, days_left: int):
    context = {
        "user": user,
        "subscription": subscription,
        "product": subscription.product,
        "days_left": days_left,
        "site_name": settings.SITE_NAME,
        "pricing_url": f"{settings.SITE_URL.rstrip('/')}{subscription.product.get_absolute_url()}pricing/",
    }
    _send("trial_expiring", context, context, user.email)


def send_payment_receipt_email(user, payment):
    context = {
        "user": user,
        "payment": payment,
        "site_name": settings.SITE_NAME,
    }
    _send("payment_receipt", context, context, user.email)
