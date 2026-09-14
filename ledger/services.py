"""Chart of accounts and double-entry posting services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable, Sequence

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from ledger.exceptions import (
    InvalidAccountError,
    InvalidLineError,
    LedgerError,
    TenantMismatchError,
    UnbalancedEntryError,
)
from ledger.models import (
    ZERO,
    Account,
    AccountType,
    JournalEntry,
    JournalEntryStatus,
    JournalLine,
)


@dataclass(frozen=True)
class JournalLineInput:
    account: Account
    debit_amount: Decimal = ZERO
    credit_amount: Decimal = ZERO
    description: str = ""


@dataclass(frozen=True)
class TrialBalanceRow:
    account_id: object
    code: str
    name: str
    account_type: str
    debit_total: Decimal
    credit_total: Decimal


def _as_money(value) -> Decimal:
    if value is None:
        return ZERO
    amount = value if isinstance(value, Decimal) else Decimal(str(value))
    return amount.quantize(Decimal("0.01"))


def _validate_line_amounts(debit: Decimal, credit: Decimal) -> None:
    if debit < ZERO or credit < ZERO:
        raise InvalidLineError("Debit and credit amounts must be non-negative.")
    if debit > ZERO and credit > ZERO:
        raise InvalidLineError("A journal line cannot have both debit and credit amounts.")
    if debit == ZERO and credit == ZERO:
        raise InvalidLineError("A journal line must have a debit or a credit amount.")


def create_account(
    *,
    organization,
    code: str,
    name: str,
    account_type: str,
    parent: Account | None = None,
    currency: str = "GHS",
    description: str = "",
    is_active: bool = True,
) -> Account:
    """Create a chart-of-accounts account for an organization."""
    if account_type not in AccountType.values:
        raise InvalidAccountError(f"Unknown account type: {account_type}")
    if parent is not None and parent.organization_id != organization.id:
        raise TenantMismatchError("Parent account belongs to a different organization.")

    account = Account(
        organization=organization,
        code=code.strip(),
        name=name.strip(),
        account_type=account_type,
        parent=parent,
        currency=(currency or "GHS").upper(),
        description=description or "",
        is_active=is_active,
    )
    account.full_clean()
    account.save()
    return account


def accounts_for_organization(organization):
    """Tenant-scoped account queryset."""
    return Account.objects.filter(organization=organization)


def _assert_accounts_in_org(organization, accounts: Iterable[Account]) -> None:
    for account in accounts:
        if account.organization_id != organization.id:
            raise TenantMismatchError(
                f"Account {account.code} does not belong to organization {organization.id}."
            )
        if not account.is_active:
            raise InvalidAccountError(f"Account {account.code} is inactive.")


def entry_totals(lines: Sequence[JournalLineInput | JournalLine]) -> tuple[Decimal, Decimal]:
    debit_total = ZERO
    credit_total = ZERO
    for line in lines:
        debit_total += _as_money(line.debit_amount)
        credit_total += _as_money(line.credit_amount)
    return debit_total, credit_total


def assert_balanced(lines: Sequence[JournalLineInput | JournalLine]) -> tuple[Decimal, Decimal]:
    if len(lines) < 2:
        raise UnbalancedEntryError("A journal entry requires at least two lines.")
    debit_total, credit_total = entry_totals(lines)
    if debit_total != credit_total:
        raise UnbalancedEntryError(
            f"Unbalanced entry: debits={debit_total} credits={credit_total}."
        )
    if debit_total == ZERO:
        raise UnbalancedEntryError("Journal entry totals cannot be zero.")
    return debit_total, credit_total


@transaction.atomic
def post_journal_entry(
    *,
    organization,
    reference: str,
    business_date: date,
    lines: Sequence[JournalLineInput],
    description: str = "",
    currency: str = "GHS",
    created_by=None,
    posted_by=None,
) -> JournalEntry:
    """
    Create and post a balanced double-entry journal in one transaction.

    Posted entries are append-only thereafter.
    """
    if not lines:
        raise InvalidLineError("At least two journal lines are required.")

    normalized: list[JournalLineInput] = []
    for raw in lines:
        debit = _as_money(raw.debit_amount)
        credit = _as_money(raw.credit_amount)
        _validate_line_amounts(debit, credit)
        normalized.append(
            JournalLineInput(
                account=raw.account,
                debit_amount=debit,
                credit_amount=credit,
                description=raw.description or "",
            )
        )

    _assert_accounts_in_org(organization, [line.account for line in normalized])
    assert_balanced(normalized)

    entry = JournalEntry.objects.create(
        organization=organization,
        reference=reference.strip(),
        business_date=business_date,
        description=description or "",
        status=JournalEntryStatus.DRAFT,
        currency=(currency or "GHS").upper(),
        created_by=created_by,
    )

    for idx, line in enumerate(normalized, start=1):
        JournalLine.objects.create(
            journal_entry=entry,
            account=line.account,
            line_no=idx,
            description=line.description,
            debit_amount=line.debit_amount,
            credit_amount=line.credit_amount,
        )

    entry.status = JournalEntryStatus.POSTED
    entry.posted_at = timezone.now()
    entry.posted_by = posted_by or created_by
    entry.save(update_fields=["status", "posted_at", "posted_by", "updated_at"])
    return entry


def trial_balance(
    organization,
    *,
    as_of: date | None = None,
) -> list[TrialBalanceRow]:
    """
    Sum posted journal activity per account for an organization.

    When ``as_of`` is set, only entries with business_date <= as_of are included.
    Across a complete set of postings, total debits equal total credits.
    """
    lines = JournalLine.objects.filter(
        journal_entry__organization=organization,
        journal_entry__status=JournalEntryStatus.POSTED,
    ).select_related("account")
    if as_of is not None:
        lines = lines.filter(journal_entry__business_date__lte=as_of)

    aggregates = (
        lines.values(
            "account_id",
            "account__code",
            "account__name",
            "account__account_type",
        )
        .annotate(
            debit_total=Sum("debit_amount"),
            credit_total=Sum("credit_amount"),
        )
        .order_by("account__code")
    )

    rows: list[TrialBalanceRow] = []
    for row in aggregates:
        rows.append(
            TrialBalanceRow(
                account_id=row["account_id"],
                code=row["account__code"],
                name=row["account__name"],
                account_type=row["account__account_type"],
                debit_total=_as_money(row["debit_total"] or ZERO),
                credit_total=_as_money(row["credit_total"] or ZERO),
            )
        )
    return rows


def trial_balance_totals(rows: Sequence[TrialBalanceRow]) -> tuple[Decimal, Decimal]:
    debit = sum((row.debit_total for row in rows), ZERO)
    credit = sum((row.credit_total for row in rows), ZERO)
    return _as_money(debit), _as_money(credit)


def assert_trial_balance_balanced(organization, *, as_of: date | None = None) -> tuple[Decimal, Decimal]:
    rows = trial_balance(organization, as_of=as_of)
    debit_total, credit_total = trial_balance_totals(rows)
    if debit_total != credit_total:
        raise LedgerError(
            f"Trial balance out of balance: debits={debit_total} credits={credit_total}."
        )
    return debit_total, credit_total
