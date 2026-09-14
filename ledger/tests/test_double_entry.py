from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from ledger.exceptions import (
    PostedEntryImmutableError,
    TenantMismatchError,
    UnbalancedEntryError,
)
from ledger.models import AccountType, JournalEntryStatus
from ledger.services import (
    JournalLineInput,
    assert_trial_balance_balanced,
    create_account,
    post_journal_entry,
    trial_balance,
    trial_balance_totals,
)
from organizations.services import create_organization


User = get_user_model()


class LedgerDoubleEntryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ledger_user",
            email="ledger@example.com",
            password="SecurePass123!",
        )
        self.org = create_organization(name="MFI Alpha", created_by=self.user)
        self.cash = create_account(
            organization=self.org,
            code="1000",
            name="Cash",
            account_type=AccountType.ASSET,
        )
        self.capital = create_account(
            organization=self.org,
            code="3000",
            name="Owner Capital",
            account_type=AccountType.EQUITY,
        )
        self.expense = create_account(
            organization=self.org,
            code="5000",
            name="Office Expense",
            account_type=AccountType.EXPENSE,
        )

    def test_create_account_unique_code_per_org(self):
        other = create_organization(name="MFI Beta", created_by=self.user)
        create_account(
            organization=other,
            code="1000",
            name="Cash Other",
            account_type=AccountType.ASSET,
        )
        with self.assertRaises(ValidationError):
            create_account(
                organization=self.org,
                code="1000",
                name="Duplicate Cash",
                account_type=AccountType.ASSET,
            )

    def test_post_balanced_entry(self):
        entry = post_journal_entry(
            organization=self.org,
            reference="JE-001",
            business_date=date(2026, 9, 1),
            description="Initial capital",
            created_by=self.user,
            lines=[
                JournalLineInput(account=self.cash, debit_amount=Decimal("1000.00")),
                JournalLineInput(account=self.capital, credit_amount=Decimal("1000.00")),
            ],
        )
        self.assertEqual(entry.status, JournalEntryStatus.POSTED)
        self.assertIsNotNone(entry.posted_at)
        self.assertEqual(entry.lines.count(), 2)

    def test_reject_unbalanced_entry(self):
        with self.assertRaises(UnbalancedEntryError):
            post_journal_entry(
                organization=self.org,
                reference="JE-BAD",
                business_date=date(2026, 9, 1),
                lines=[
                    JournalLineInput(account=self.cash, debit_amount=Decimal("100.00")),
                    JournalLineInput(account=self.capital, credit_amount=Decimal("50.00")),
                ],
            )
        self.assertEqual(self.org.journal_entries.count(), 0)

    def test_reject_cross_tenant_account(self):
        other = create_organization(name="Other Org", created_by=self.user)
        other_cash = create_account(
            organization=other,
            code="1000",
            name="Other Cash",
            account_type=AccountType.ASSET,
        )
        with self.assertRaises(TenantMismatchError):
            post_journal_entry(
                organization=self.org,
                reference="JE-XORG",
                business_date=date(2026, 9, 1),
                lines=[
                    JournalLineInput(account=other_cash, debit_amount=Decimal("10.00")),
                    JournalLineInput(account=self.capital, credit_amount=Decimal("10.00")),
                ],
            )

    def test_posted_entry_is_append_only(self):
        entry = post_journal_entry(
            organization=self.org,
            reference="JE-002",
            business_date=date(2026, 9, 2),
            created_by=self.user,
            lines=[
                JournalLineInput(account=self.expense, debit_amount=Decimal("25.00")),
                JournalLineInput(account=self.cash, credit_amount=Decimal("25.00")),
            ],
        )
        entry.description = "tamper"
        with self.assertRaises(PostedEntryImmutableError):
            entry.save()
        line = entry.lines.first()
        line.description = "tamper line"
        with self.assertRaises(PostedEntryImmutableError):
            line.save()
        with self.assertRaises(PostedEntryImmutableError):
            entry.delete()

    def test_trial_balance_balances_after_postings(self):
        post_journal_entry(
            organization=self.org,
            reference="JE-TB-1",
            business_date=date(2026, 9, 1),
            lines=[
                JournalLineInput(account=self.cash, debit_amount=Decimal("500.00")),
                JournalLineInput(account=self.capital, credit_amount=Decimal("500.00")),
            ],
        )
        post_journal_entry(
            organization=self.org,
            reference="JE-TB-2",
            business_date=date(2026, 9, 3),
            lines=[
                JournalLineInput(account=self.expense, debit_amount=Decimal("40.00")),
                JournalLineInput(account=self.cash, credit_amount=Decimal("40.00")),
            ],
        )

        rows = trial_balance(self.org)
        debit_total, credit_total = trial_balance_totals(rows)
        self.assertEqual(debit_total, credit_total)
        self.assertEqual(debit_total, Decimal("540.00"))

        cash_row = next(row for row in rows if row.code == "1000")
        self.assertEqual(cash_row.debit_total, Decimal("500.00"))
        self.assertEqual(cash_row.credit_total, Decimal("40.00"))

        as_of_rows = trial_balance(self.org, as_of=date(2026, 9, 1))
        as_of_debit, as_of_credit = trial_balance_totals(as_of_rows)
        self.assertEqual(as_of_debit, as_of_credit)
        self.assertEqual(as_of_debit, Decimal("500.00"))

        assert_trial_balance_balanced(self.org)

    def test_trial_balance_is_tenant_isolated(self):
        other_user = User.objects.create_user(
            username="other_ledger",
            email="other-ledger@example.com",
            password="SecurePass123!",
        )
        other_org = create_organization(name="Isolated Org", created_by=other_user)
        other_cash = create_account(
            organization=other_org,
            code="1000",
            name="Cash",
            account_type=AccountType.ASSET,
        )
        other_equity = create_account(
            organization=other_org,
            code="3000",
            name="Capital",
            account_type=AccountType.EQUITY,
        )
        post_journal_entry(
            organization=self.org,
            reference="JE-A",
            business_date=date(2026, 9, 1),
            lines=[
                JournalLineInput(account=self.cash, debit_amount=Decimal("100.00")),
                JournalLineInput(account=self.capital, credit_amount=Decimal("100.00")),
            ],
        )
        post_journal_entry(
            organization=other_org,
            reference="JE-B",
            business_date=date(2026, 9, 1),
            lines=[
                JournalLineInput(account=other_cash, debit_amount=Decimal("999.00")),
                JournalLineInput(account=other_equity, credit_amount=Decimal("999.00")),
            ],
        )

        rows = trial_balance(self.org)
        debit_total, credit_total = trial_balance_totals(rows)
        self.assertEqual(debit_total, Decimal("100.00"))
        self.assertEqual(credit_total, Decimal("100.00"))
        self.assertTrue(all(row.code in {"1000", "3000"} for row in rows))
