"""Tests for HTTP error -> typed exception mapping."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from kosovopay import KosovoPay
from kosovopay.exceptions import (
    AmountBelowMinimumError,
    ApiError,
    AuthenticationError,
    BankNotEnabledError,
    BankUnreachableError,
    IdempotencyError,
    PartialRefundUnsupportedError,
    PaymentError,
    PaymentNotCancelableError,
    PaymentNotRefundableError,
    PermissionError,
    RateLimitError,
    RefundExceedsRemainingError,
    ValidationError,
)
from tests.conftest import make_error


def _client() -> KosovoPay:
    return KosovoPay("sk_test_abc")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _err_response(status: int, body: dict[str, Any], retry_after: int | None = None) -> httpx.Response:
    headers = {}
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    return httpx.Response(status, json=body, headers=headers)


# ---------------------------------------------------------------------------
# Type-family mapping
# ---------------------------------------------------------------------------


def test_401_maps_to_authentication_error(respx_mock: Any) -> None:
    respx_mock.get("/me").mock(
        return_value=_err_response(401, make_error("authentication_error"))
    )
    kp = _client()
    with pytest.raises(AuthenticationError) as exc_info:
        kp.me()
    assert exc_info.value.status_code == 401


def test_403_maps_to_permission_error(respx_mock: Any) -> None:
    respx_mock.get("/me").mock(
        return_value=_err_response(403, make_error("permission_error", message="Forbidden."))
    )
    kp = _client()
    with pytest.raises(PermissionError) as exc_info:
        kp.me()
    assert exc_info.value.status_code == 403


def test_422_maps_to_validation_error(respx_mock: Any) -> None:
    respx_mock.get("/me").mock(
        return_value=_err_response(422, make_error("validation_error", message="Invalid param."))
    )
    kp = _client()
    with pytest.raises(ValidationError):
        kp.me()


def test_idempotency_error_maps_correctly(respx_mock: Any) -> None:
    respx_mock.get("/me").mock(
        return_value=_err_response(409, make_error("idempotency_error"))
    )
    kp = _client()
    with pytest.raises(IdempotencyError):
        kp.me()


def test_payment_error_type_maps_to_payment_error(respx_mock: Any) -> None:
    respx_mock.get("/me").mock(
        return_value=_err_response(402, make_error("payment_error"))
    )
    kp = _client()
    with pytest.raises(PaymentError):
        kp.me()


def test_unknown_type_falls_back_to_api_error(respx_mock: Any) -> None:
    respx_mock.get("/me").mock(
        return_value=_err_response(500, make_error("totally_unknown_type"))
    )
    kp = _client()
    with pytest.raises(ApiError):
        kp.me()


# ---------------------------------------------------------------------------
# Rate limit
# ---------------------------------------------------------------------------


def test_429_maps_to_rate_limit_error(respx_mock: Any) -> None:
    respx_mock.get("/me").mock(
        return_value=_err_response(
            429,
            make_error("rate_limit_error"),
            retry_after=7,
        )
    )
    kp = _client()
    with pytest.raises(RateLimitError) as exc_info:
        kp.me()
    assert exc_info.value.retry_after == 7
    assert exc_info.value.status_code == 429


def test_429_without_retry_after_header(respx_mock: Any) -> None:
    respx_mock.get("/me").mock(
        return_value=_err_response(429, make_error("rate_limit_error"))
    )
    kp = _client()
    with pytest.raises(RateLimitError) as exc_info:
        kp.me()
    assert exc_info.value.retry_after is None


# ---------------------------------------------------------------------------
# Payment subcode mapping (exact code match)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("code", "exc_cls"),
    [
        ("amount_below_minimum", AmountBelowMinimumError),
        ("bank_not_enabled", BankNotEnabledError),
        ("bank_unreachable", BankUnreachableError),
        ("payment_not_cancelable", PaymentNotCancelableError),
        ("payment_not_refundable", PaymentNotRefundableError),
        ("refund_exceeds_remaining", RefundExceedsRemainingError),
        ("partial_refund_unsupported", PartialRefundUnsupportedError),
    ],
)
def test_payment_subcode_maps_to_specific_exception(
    respx_mock: Any, code: str, exc_cls: type
) -> None:
    respx_mock.get("/me").mock(
        return_value=_err_response(
            422,
            make_error("payment_error", code=code),
        )
    )
    kp = _client()
    with pytest.raises(exc_cls):
        kp.me()


def test_unknown_code_with_payment_type_falls_back_to_payment_error(
    respx_mock: Any,
) -> None:
    """An unknown code with payment_error type falls back to PaymentError (not ApiError)."""
    respx_mock.get("/me").mock(
        return_value=_err_response(
            422,
            make_error("payment_error", code="some_future_code"),
        )
    )
    kp = _client()
    with pytest.raises(PaymentError):
        kp.me()


def test_unknown_code_unknown_type_falls_back_to_api_error(respx_mock: Any) -> None:
    """No code and no known type -> ApiError."""
    respx_mock.get("/me").mock(
        return_value=httpx.Response(500, json={})
    )
    kp = _client()
    with pytest.raises(ApiError):
        kp.me()
