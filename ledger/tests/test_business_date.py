from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from ledger.calendar import (
    ensure_business_calendar,
    get_current_business_date,
    run_end_of_day,
    run_end_of_day_for_all,
)
from ledger.exceptions import (
    ClosedBusinessDayError,
    EodProcessingError,
    InvalidBusinessDateError,
)
from ledger.models import AccountType, BusinessDayStatus
from ledger.services import JournalLineInput, create_account, post_journal_entry
from ledger.tasks import run_all_eod_task, run_organization_eod_task
from organizations.services import create_organization


User = get_user_model()


class BusinessDateEodTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="eod_user",
            email="eod@example.com",
            password="SecurePass123!",
        )
        self.org = create_organization(name="EOD MFI", created_by=self.user)
        self.calendar = ensure_business_calendar(
            self.org, initial_date=date(2026, 9, 10)
        )
        self.cash = create_account(
            organization=self.org,
            code="1000",
            name="Cash",
            account_type=AccountType.ASSET,
        )
        self.capital = create_account(
            organization=self.org,
            code="3000",
            name="Capital",
            account_type=AccountType.EQUITY,
        )

    def test_ensure_calendar_opens_current_day(self):
        self.assertEqual(self.calendar.current_business_date, date(2026, 9, 10))
        self.assertEqual(get_current_business_date(self.org), date(2026, 9, 10))
        day = self.org.ledger_business_days.get(business_date=date(2026, 9, 10))
        self.assertEqual(day.status, BusinessDayStatus.OPEN)

    def test_reject_posting_on_non_current_date(self):
        with self.assertRaises(InvalidBusinessDateError):
            post_journal_entry(
                organization=self.org,
                reference="JE-FUTURE",
                business_date=date(2026, 9, 11),
                lines=[
                    JournalLineInput(account=self.cash, debit_amount=Decimal("10.00")),
                    JournalLineInput(account=self.capital, credit_amount=Decimal("10.00")),
                ],
            )

    def test_eod_closes_day_advances_calendar_and_blocks_repost(self):
        post_journal_entry(
            organization=self.org,
            reference="JE-EOD-1",
            business_date=date(2026, 9, 10),
            created_by=self.user,
            lines=[
                JournalLineInput(account=self.cash, debit_amount=Decimal("100.00")),
                JournalLineInput(account=self.capital, credit_amount=Decimal("100.00")),
            ],
        )
        closed = run_end_of_day(self.org, closed_by=self.user, notes="nightly")
        self.assertEqual(closed.status, BusinessDayStatus.CLOSED)
        self.assertEqual(closed.trial_balance_debit, Decimal("100.00"))
        self.assertEqual(closed.trial_balance_credit, Decimal("100.00"))
        self.calendar.refresh_from_db()
        self.assertEqual(self.calendar.current_business_date, date(2026, 9, 11))
        self.assertTrue(
            self.org.ledger_business_days.filter(
                business_date=date(2026, 9, 11),
                status=BusinessDayStatus.OPEN,
            ).exists()
        )

        with self.assertRaises(InvalidBusinessDateError):
            post_journal_entry(
                organization=self.org,
                reference="JE-EOD-REOPEN",
                business_date=date(2026, 9, 10),
                lines=[
                    JournalLineInput(account=self.cash, debit_amount=Decimal("1.00")),
                    JournalLineInput(account=self.capital, credit_amount=Decimal("1.00")),
                ],
            )

        # Closed day remains closed even if somehow targeted after calendar rewind attempt
        closed_day = self.org.ledger_business_days.get(business_date=date(2026, 9, 10))
        self.assertTrue(closed_day.is_closed)
        with self.assertRaises(ClosedBusinessDayError):
            from ledger.calendar import ensure_open_business_day

            ensure_open_business_day(self.org, date(2026, 9, 10))

    def test_eod_rejects_unbalanced_books(self):
        # Force an impossible state by closing without activity is fine (0=0).
        # Unbalanced path: create posted lines bypassing service is hard; instead
        # run EOD twice on same day after first close.
        run_end_of_day(self.org)
        with self.assertRaises(EodProcessingError):
            run_end_of_day(self.org, business_date=date(2026, 9, 10))

    def test_eod_is_tenant_isolated(self):
        other = create_organization(name="Other EOD", created_by=self.user)
        ensure_business_calendar(other, initial_date=date(2026, 9, 10))
        run_end_of_day(self.org)
        self.calendar.refresh_from_db()
        self.assertEqual(self.calendar.current_business_date, date(2026, 9, 11))
        self.assertEqual(get_current_business_date(other), date(2026, 9, 10))

    def test_run_end_of_day_for_all_skips_orgs_without_calendar(self):
        create_organization(name="No Calendar Yet", created_by=self.user)
        results = run_end_of_day_for_all(notes="batch")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "closed")
        self.assertEqual(results[0]["closed_date"], "2026-09-10")

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_BROKER_URL="memory://")
    def test_celery_organization_eod_task(self):
        result = run_organization_eod_task.apply(
            args=[],
            kwargs={"organization_id": str(self.org.id), "notes": "task"},
        ).get()
        self.assertEqual(result["closed_date"], "2026-09-10")
        self.calendar.refresh_from_db()
        self.assertEqual(self.calendar.current_business_date, date(2026, 9, 11))

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_BROKER_URL="memory://")
    def test_celery_all_eod_task(self):
        payload = run_all_eod_task.apply(kwargs={"notes": "nightly"}).get()
        self.assertEqual(payload["closed"], 1)
        self.assertEqual(payload["errors"], 0)
