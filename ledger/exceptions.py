"""Ledger domain errors."""


class LedgerError(Exception):
    """Base error for ledger operations."""


class UnbalancedEntryError(LedgerError):
    """Debits do not equal credits."""


class TenantMismatchError(LedgerError):
    """Account or line does not belong to the journal organization."""


class InvalidAccountError(LedgerError):
    """Account is missing, inactive, or otherwise unusable for posting."""


class PostedEntryImmutableError(LedgerError):
    """Posted journal entries and lines cannot be modified or deleted."""


class InvalidLineError(LedgerError):
    """A journal line fails debit/credit validation rules."""
