"""Decimal helpers for currency-safe calculations."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

MONEY_QUANT = Decimal("0.01")
ZERO = Decimal("0")


def quantize_money(value: Decimal | str | int | float) -> Decimal:
    """Normalize a monetary value to two decimal places."""
    return Decimal(str(value)).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def to_minor_units(amount: Decimal | str | int | float, factor: int = 100) -> int:
    """Convert major currency units to minor units (e.g. dollars to cents)."""
    return int(quantize_money(amount) * factor)


def to_api_amount(amount: Decimal | str | int | float) -> float:
    """Convert Decimal to float for payment gateway JSON payloads."""
    return float(quantize_money(amount))
