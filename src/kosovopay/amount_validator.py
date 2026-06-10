"""Client-side amount pre-validation against a bank's live capabilities.

Mirrors the server's bank min/step checks so callers can catch
``amount_below_minimum`` / ``amount_step_invalid`` before a round-trip.
"""

from __future__ import annotations

from kosovopay.enums import CurrencyCode
from kosovopay.models import AmountValidation, Bank


def validate_amount(bank: Bank, amount: int, currency: CurrencyCode) -> AmountValidation:
    """Pre-check *amount* against *bank*'s live capabilities.

    Returns an :class:`~kosovopay.models.AmountValidation` with ``valid=True``
    when the amount passes all checks, or a descriptive failure otherwise.
    """
    caps = bank.capabilities

    # Currency support check
    if caps.currencies and currency not in caps.currencies:
        return AmountValidation(
            valid=False,
            code="currency_not_supported",
            message=f"{bank.display_name} does not support {currency.value}.",
        )

    # Minimum amount check
    if amount < caps.min_amount:
        return AmountValidation(
            valid=False,
            code="amount_below_minimum",
            message=(
                f"Amount is below the {bank.display_name} minimum of {caps.min_amount}."
            ),
        )

    # Step check
    step = max(1, caps.amount_step)
    if amount % step != 0:
        lower = (amount // step) * step
        upper = lower + step
        return AmountValidation(
            valid=False,
            code="amount_step_invalid",
            message=f"{bank.display_name} requires amounts in steps of {step}.",
            nearest_valid=[lower, upper],
        )

    return AmountValidation(valid=True)
