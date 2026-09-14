"""Organization business-date calendar and end-of-day processing."""

from __future__ import annotations

from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone

from ledger.exceptions import (
    ClosedBusinessDayError,
    EodProcessingError,
    InvalidBusinessDateError,
    LedgerError,
)
from ledger.models import BusinessCalendar, BusinessDay, BusinessDayStatus
from ledger.services import assert_trial_balance_balanced


def _today() -> date:
    return timezone.localdate()


@transaction.atomic
def ensure_business_calendar(
    organization,
    *,
    initial_date: date | None = None,
    timezone_name: str = "Africa/Accra",
) -> BusinessCalendar:
    """
    Ensure the organization has a ledger calendar and an open current business day.
    """
    calendar, created = BusinessCalendar.objects.select_for_update().get_or_create(
        organization=organization,
        defaults={
            "current_business_date": initial_date or _today(),
            "timezone_name": timezone_name or "Africa/Accra",
        },
    )
    ensure_open_business_day(organization, calendar.current_business_date)
    return calendar


def get_current_business_date(organization) -> date:
    """Return the organization's current ledger business date (creating calendar if needed)."""
    return ensure_business_calendar(organization).current_business_date


def ensure_open_business_day(organization, business_date: date) -> BusinessDay:
    """Get or create an OPEN business day row for the given date."""
    day, created = BusinessDay.objects.get_or_create(
        organization=organization,
        business_date=business_date,
        defaults={
            "status": BusinessDayStatus.OPEN,
            "opened_at": timezone.now(),
        },
    )
    if not created and day.is_closed:
        raise ClosedBusinessDayError(
            f"Business day {business_date.isoformat()} is closed for this organization."
        )
    return day


def assert_posting_allowed(organization, business_date: date) -> BusinessDay:
    """
    Validate that journals may be posted for ``business_date``.

    Rules for this slice:
    - Calendar exists (created on demand)
    - Posting is allowed only on the organization's current open business date
    - Closed days reject posting
    """
    calendar = ensure_business_calendar(organization)
    if business_date != calendar.current_business_date:
        raise InvalidBusinessDateError(
            f"Posting allowed only on current business date "
            f"{calendar.current_business_date.isoformat()} "
            f"(got {business_date.isoformat()})."
        )
    return ensure_open_business_day(organization, business_date)


@transaction.atomic
def run_end_of_day(
    organization,
    *,
    business_date: date | None = None,
    closed_by=None,
    notes: str = "",
) -> BusinessDay:
    """
    Close the organization's current (or specified) open business day and advance.

    Steps:
    1. Lock calendar
    2. Require the day to be the current open business date
    3. Assert trial balance balances as-of that date
    4. Mark day CLOSED with TB snapshot
    5. Advance ``current_business_date`` by one calendar day and open the next day

    Period/month close is Phase 3.13 and is intentionally not implemented here.
    """
    calendar = (
        BusinessCalendar.objects.select_for_update()
        .filter(organization=organization)
        .first()
    )
    if calendar is None:
        calendar = ensure_business_calendar(organization)

    target = business_date or calendar.current_business_date
    if target != calendar.current_business_date:
        raise EodProcessingError(
            f"EOD target {target.isoformat()} must match current business date "
            f"{calendar.current_business_date.isoformat()}."
        )

    day = (
        BusinessDay.objects.select_for_update()
        .filter(organization=organization, business_date=target)
        .first()
    )
    if day is None:
        day = ensure_open_business_day(organization, target)
        day = BusinessDay.objects.select_for_update().get(pk=day.pk)

    if day.is_closed:
        raise EodProcessingError(f"Business day {target.isoformat()} is already closed.")

    try:
        debit_total, credit_total = assert_trial_balance_balanced(
            organization, as_of=target
        )
    except LedgerError as exc:
        raise EodProcessingError(str(exc)) from exc

    day.status = BusinessDayStatus.CLOSED
    day.closed_at = timezone.now()
    day.closed_by = closed_by
    day.notes = notes or day.notes
    day.trial_balance_debit = debit_total
    day.trial_balance_credit = credit_total
    day.save(
        update_fields=[
            "status",
            "closed_at",
            "closed_by",
            "notes",
            "trial_balance_debit",
            "trial_balance_credit",
            "updated_at",
        ]
    )

    next_date = target + timedelta(days=1)
    calendar.current_business_date = next_date
    calendar.save(update_fields=["current_business_date", "updated_at"])
    ensure_open_business_day(organization, next_date)
    return day


def run_end_of_day_for_all(*, closed_by=None, notes: str = "") -> list[dict]:
    """
    Run EOD for every organization that already has a ledger calendar.

    Organizations without a calendar are skipped (no implicit calendar creation).
    """
    results: list[dict] = []
    calendars = BusinessCalendar.objects.select_related("organization").order_by(
        "organization__name"
    )
    for calendar in calendars:
        org = calendar.organization
        try:
            day = run_end_of_day(org, closed_by=closed_by, notes=notes)
            results.append(
                {
                    "organization_id": str(org.id),
                    "organization": org.name,
                    "closed_date": day.business_date.isoformat(),
                    "status": "closed",
                }
            )
        except Exception as exc:  # noqa: BLE001 - collect per-tenant failures
            results.append(
                {
                    "organization_id": str(org.id),
                    "organization": org.name,
                    "closed_date": calendar.current_business_date.isoformat(),
                    "status": "error",
                    "error": str(exc),
                }
            )
    return results
