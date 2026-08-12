from decimal import Decimal, InvalidOperation

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()


@register.filter
def format_cedi(value, decimals=0):
    """Format a numeric value as Ghanaian Cedi (GH₵)."""
    try:
        amount = Decimal(str(value or 0))
    except (InvalidOperation, TypeError, ValueError):
        return "GH₵0"

    quant = Decimal("1") if int(decimals) == 0 else Decimal(f"1.{'0' * int(decimals)}")
    amount = amount.quantize(quant)
    if int(decimals) == 0:
        display = intcomma(int(amount))
    else:
        display = intcomma(f"{amount:.{int(decimals)}f}")
    return f"GH₵{display}"
