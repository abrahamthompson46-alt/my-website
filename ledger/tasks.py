"""Celery tasks for ledger end-of-day processing."""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="ledger.run_organization_eod",
    acks_late=True,
)
def run_organization_eod_task(self, organization_id: str, notes: str = ""):
    from organizations.models import Organization
    from ledger.calendar import run_end_of_day

    organization = Organization.objects.get(pk=organization_id)
    day = run_end_of_day(organization, notes=notes)
    logger.info(
        "Closed business day %s for organization %s",
        day.business_date.isoformat(),
        organization_id,
    )
    return {
        "organization_id": organization_id,
        "closed_date": day.business_date.isoformat(),
        "status": day.status,
    }


@shared_task(
    bind=True,
    name="ledger.run_all_eod",
    acks_late=True,
)
def run_all_eod_task(self, notes: str = ""):
    from ledger.calendar import run_end_of_day_for_all

    results = run_end_of_day_for_all(notes=notes)
    closed = sum(1 for row in results if row.get("status") == "closed")
    errors = sum(1 for row in results if row.get("status") == "error")
    logger.info("Ledger EOD batch finished: closed=%s errors=%s", closed, errors)
    return {"closed": closed, "errors": errors, "results": results}
