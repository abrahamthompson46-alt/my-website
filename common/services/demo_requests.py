"""Shared demo request validation, rate limiting, and audit logging."""

from __future__ import annotations

import logging
from datetime import timedelta

from django.utils import timezone

from accounts.models import AuditEventType
from accounts.services.audit import log_audit_event
from accounts.services.rate_limit import check_auth_rate_limit, log_rate_limit_exceeded
from products.models import ProductDemoRequest

logger = logging.getLogger(__name__)


DEMO_RATE_LIMIT = 5
DEMO_RATE_WINDOW = 3600
DUPLICATE_WINDOW_HOURS = 24


def is_demo_rate_limited(request) -> bool:
    return check_auth_rate_limit(
        request,
        scope="demo-submit",
        limit=DEMO_RATE_LIMIT,
        window_seconds=DEMO_RATE_WINDOW,
    )


def log_demo_rate_limit(request):
    log_rate_limit_exceeded(request, "demo-submit")


def is_duplicate_demo(*, work_email: str, product_id=None) -> bool:
    since = timezone.now() - timedelta(hours=DUPLICATE_WINDOW_HOURS)
    qs = ProductDemoRequest.objects.filter(work_email__iexact=work_email.strip(), created_at__gte=since)
    if product_id:
        qs = qs.filter(product_id=product_id)
    return qs.exists()


def log_demo_submission(request, demo: ProductDemoRequest):
    log_audit_event(
        AuditEventType.DEMO_REQUEST_SUBMITTED,
        request=request,
        message=f"Demo request from {demo.work_email}",
        metadata={
            "demo_id": str(demo.pk),
            "product_id": str(demo.product_id) if demo.product_id else None,
            "company": demo.company,
            "source": demo.source,
        },
    )
    try:
        from common.services.owner_notifications import notify_owners_demo_request

        notify_owners_demo_request(demo)
    except Exception:
        logger.exception("Failed to notify platform owners about demo request %s", demo.pk)
