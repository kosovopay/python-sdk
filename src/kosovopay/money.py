"""Integer-only money helpers.

Amounts are always minor units (e.g. cents); rates are decimal strings.
No floats are stored — only a final ``round()`` to int for conversion.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from kosovopay.models import Currency


def format_amount(amount: int, decimals: int, symbol: str = "") -> str:
    """Format minor units as a human-readable string.

    Examples::

        format_amount(4990, 2, "€")  # "€49.90"
        format_amount(100, 0, "$")   # "$100"
    """
    negative = amount < 0
    abs_amount = abs(amount)
    divisor = 10**decimals
    major = abs_amount // divisor
    minor = abs_amount % divisor

    formatted = f"{major}.{str(minor).zfill(decimals)}" if decimals > 0 else str(major)

    sign = "-" if negative else ""
    return f"{sign}{symbol}{formatted}"


def format_currency(amount: int, currency: Currency) -> str:
    """Format *amount* using a :class:`~kosovopay.models.Currency` DTO."""
    return format_amount(amount, currency.decimals, currency.symbol or "")


def convert(amount: int, rate: str) -> int:
    """Convert *amount* (minor units) by a decimal *rate* string.

    Uses :class:`decimal.Decimal` for precision; rounds half-up to int.

    Example::

        convert(10000, "1.12")  # 11200
    """
    try:
        d_rate = Decimal(rate)
    except Exception:
        d_rate = Decimal("0")
    result = Decimal(amount) * d_rate
    return int(result.to_integral_value(rounding=ROUND_HALF_UP))
