"""Celery tasks for email delivery and payment webhooks."""

from __future__ import annotations

import base64
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="common.send_platform_mail",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    acks_late=True,
)
def send_platform_mail_task(
    self,
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
    from control_room.services.email_delivery import send_platform_mail

    return send_platform_mail(
        subject=subject,
        message=message,
        recipient_list=recipient_list,
        from_email=from_email,
        from_name=from_name,
        html_message=html_message,
        reply_to=reply_to,
        headers=headers,
        fail_silently=fail_silently,
    )


@shared_task(
    bind=True,
    name="payments.process_webhook",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
    acks_late=True,
)
def process_webhook_task(
    self,
    gateway_code: str,
    payload: dict,
    raw_body_b64: str,
    headers: dict,
):
    from payments.models import GatewayConfiguration
    from payments.services.webhooks import process_webhook

    gateway_config = GatewayConfiguration.objects.get(code=gateway_code, is_active=True)
    raw_body = base64.b64decode(raw_body_b64.encode("ascii"))
    event, created = process_webhook(gateway_config, payload, raw_body, headers)
    return {"event_id": event.pk, "created": created, "processed": event.processed}
