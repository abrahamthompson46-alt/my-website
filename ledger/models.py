"""Organization-scoped chart of accounts and double-entry journal models."""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from core.models import BaseModel
from ledger.exceptions import PostedEntryImmutableError


ZERO = Decimal("0.00")


class AccountType(models.TextChoices):
    ASSET = "asset", "Asset"
    LIABILITY = "liability", "Liability"
    EQUITY = "equity", "Equity"
    INCOME = "income", "Income"
    EXPENSE = "expense", "Expense"


class JournalEntryStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    POSTED = "posted", "Posted"


class Account(BaseModel):
    """Chart-of-accounts node scoped to a single organization."""

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="ledger_accounts",
    )
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=AccountType.choices)
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
    )
    is_active = models.BooleanField(default=True)
    currency = models.CharField(max_length=3, default="GHS")
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["organization", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"],
                name="uniq_ledger_account_org_code",
            ),
        ]
        indexes = [
            models.Index(fields=["organization", "account_type"]),
            models.Index(fields=["organization", "is_active"]),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"

    def clean(self):
        super().clean()
        if self.parent_id:
            if self.parent.organization_id != self.organization_id:
                raise ValidationError({"parent": "Parent account must belong to the same organization."})
            if self.parent_id == self.pk:
                raise ValidationError({"parent": "An account cannot be its own parent."})


class JournalEntry(BaseModel):
    """Header for a multi-line journal; posted rows are append-only."""

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="journal_entries",
    )
    reference = models.CharField(max_length=64)
    business_date = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20,
        choices=JournalEntryStatus.choices,
        default=JournalEntryStatus.DRAFT,
    )
    currency = models.CharField(max_length=3, default="GHS")
    posted_at = models.DateTimeField(null=True, blank=True)
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posted_journal_entries",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_journal_entries",
    )

    class Meta:
        ordering = ["-business_date", "-created_at"]
        verbose_name_plural = "journal entries"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "reference"],
                name="uniq_ledger_journal_org_reference",
            ),
        ]
        indexes = [
            models.Index(fields=["organization", "business_date"]),
            models.Index(fields=["organization", "status"]),
        ]

    def __str__(self):
        return f"{self.reference} ({self.status})"

    @property
    def is_posted(self) -> bool:
        return self.status == JournalEntryStatus.POSTED

    def save(self, *args, **kwargs):
        if not self._state.adding:
            previous = JournalEntry.objects.filter(pk=self.pk).values_list("status", flat=True).first()
            if previous == JournalEntryStatus.POSTED:
                raise PostedEntryImmutableError("Posted journal entries cannot be modified.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_posted or (
            not self._state.adding
            and JournalEntry.objects.filter(pk=self.pk, status=JournalEntryStatus.POSTED).exists()
        ):
            raise PostedEntryImmutableError("Posted journal entries cannot be deleted.")
        return super().delete(*args, **kwargs)


class JournalLine(BaseModel):
    """Single debit or credit leg of a journal entry."""

    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="journal_lines",
    )
    line_no = models.PositiveSmallIntegerField()
    description = models.CharField(max_length=255, blank=True)
    debit_amount = models.DecimalField(max_digits=14, decimal_places=2, default=ZERO)
    credit_amount = models.DecimalField(max_digits=14, decimal_places=2, default=ZERO)

    class Meta:
        ordering = ["journal_entry", "line_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["journal_entry", "line_no"],
                name="uniq_ledger_journal_line_no",
            ),
            models.CheckConstraint(
                check=Q(debit_amount__gte=0) & Q(credit_amount__gte=0),
                name="ledger_line_amounts_non_negative",
            ),
            models.CheckConstraint(
                check=~(Q(debit_amount__gt=0) & Q(credit_amount__gt=0)),
                name="ledger_line_not_both_debit_credit",
            ),
            models.CheckConstraint(
                check=Q(debit_amount__gt=0) | Q(credit_amount__gt=0),
                name="ledger_line_has_debit_or_credit",
            ),
        ]
        indexes = [
            models.Index(fields=["account", "journal_entry"]),
        ]

    def __str__(self):
        side = f"Dr {self.debit_amount}" if self.debit_amount else f"Cr {self.credit_amount}"
        return f"Line {self.line_no}: {self.account.code} {side}"

    def _assert_entry_mutable(self):
        if not self.journal_entry_id:
            return
        status = (
            JournalEntry.objects.filter(pk=self.journal_entry_id)
            .values_list("status", flat=True)
            .first()
        )
        if status == JournalEntryStatus.POSTED:
            raise PostedEntryImmutableError(
                "Lines on posted journal entries cannot be modified or deleted."
            )

    def save(self, *args, **kwargs):
        self._assert_entry_mutable()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._assert_entry_mutable()
        return super().delete(*args, **kwargs)
