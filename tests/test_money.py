"""Tests for money helpers and client-side amount validation."""

from __future__ import annotations

from kosovopay import convert, format_amount, validate_amount
from kosovopay.enums import BankCode, CurrencyCode
from kosovopay.models import Bank, BankCapabilities, RefundCapability

# ---------------------------------------------------------------------------
# format_amount
# ---------------------------------------------------------------------------


def test_format_amount_two_decimals() -> None:
    assert format_amount(4990, 2, "€") == "€49.90"


def test_format_amount_small_minor_unit() -> None:
    assert format_amount(5, 2, "€") == "€0.05"


def test_format_amount_negative() -> None:
    assert format_amount(-1250, 2, "$") == "-$12.50"


def test_format_amount_zero_decimals() -> None:
    assert format_amount(500, 0, "¥") == "¥500"


def test_format_amount_no_symbol() -> None:
    assert format_amount(1000, 2, "") == "10.00"


def test_format_amount_zero() -> None:
    assert format_amount(0, 2, "€") == "€0.00"


# ---------------------------------------------------------------------------
# convert
# ---------------------------------------------------------------------------


def test_convert_by_rate() -> None:
    assert convert(4990, "0.9234") == 4608


def test_convert_identity_rate() -> None:
    assert convert(10000, "1.0") == 10000


def test_convert_multiplies_correctly() -> None:
    assert convert(10000, "1.12") == 11200


def test_convert_rounds_half_up() -> None:
    # 100 * 1.005 = 100.5 -> rounds to 101
    assert convert(100, "1.005") == 101


def test_convert_invalid_rate_returns_zero() -> None:
    assert convert(1000, "not-a-number") == 0


# ---------------------------------------------------------------------------
# validate_amount (client-side)
# ---------------------------------------------------------------------------


def _make_bank(
    min_amount: int = 150,
    amount_step: int = 50,
    currencies: list[CurrencyCode] | None = None,
    partial_refunds: bool = False,
) -> Bank:
    if currencies is None:
        currencies = [CurrencyCode.EUR]
    caps = BankCapabilities(
        currencies=currencies,
        min_amount=min_amount,
        amount_step=amount_step,
        refunds=RefundCapability(supported=True, partial=partial_refunds),
    )
    return Bank(
        code=BankCode.Onefor,
        display_name="Onefor",
        logo_url=None,
        enabled=True,
        modes=[],
        capabilities=caps,
    )


def test_validate_amount_valid() -> None:
    bank = _make_bank(min_amount=150, amount_step=50)
    result = validate_amount(bank, 200, CurrencyCode.EUR)
    assert result.valid is True
    assert result.code is None


def test_validate_amount_below_minimum() -> None:
    bank = _make_bank(min_amount=150, amount_step=50)
    result = validate_amount(bank, 100, CurrencyCode.EUR)
    assert result.valid is False
    assert result.code == "amount_below_minimum"


def test_validate_amount_step_invalid() -> None:
    bank = _make_bank(min_amount=150, amount_step=50)
    result = validate_amount(bank, 173, CurrencyCode.EUR)
    assert result.valid is False
    assert result.code == "amount_step_invalid"
    assert result.nearest_valid == [150, 200]


def test_validate_amount_currency_not_supported() -> None:
    bank = _make_bank(currencies=[CurrencyCode.EUR])
    result = validate_amount(bank, 200, CurrencyCode.USD)
    assert result.valid is False
    assert result.code == "currency_not_supported"


def test_validate_amount_exact_minimum_is_valid() -> None:
    bank = _make_bank(min_amount=150, amount_step=50)
    result = validate_amount(bank, 150, CurrencyCode.EUR)
    assert result.valid is True
