"""Shared fixtures and helpers for the KosovoPay Python SDK test suite."""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

import pytest
import respx

from kosovopay import KosovoPay
from kosovopay._http import _BASE_URL

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_payment(
    id: str = "pi_test",
    status: str = "captured",
    amount: int = 1500,
    amount_captured: int = 1500,
    amount_refunded: int = 0,
    currency: str = "EUR",
    created: int = 1749600000,
) -> dict[str, Any]:
    return {
        "object": "payment",
        "id": id,
        "status": status,
        "mode": "test",
        "amount": amount,
        "amount_captured": amount_captured,
        "amount_refunded": amount_refunded,
        "currency": currency,
        "created": created,
        "refunds": [],
    }


def make_refund(
    id: str = "re_test",
    payment: str = "pi_test",
    amount: int = 500,
    status: str = "succeeded",
) -> dict[str, Any]:
    return {
        "object": "refund",
        "id": id,
        "payment": payment,
        "amount": amount,
        "status": status,
        "reason": None,
        "failure_reason": None,
        "created": 1749600000,
        "succeeded_at": 1749600001,
    }


def make_list(data: list[dict[str, Any]], has_more: bool = False) -> dict[str, Any]:
    return {
        "object": "list",
        "data": data,
        "has_more": has_more,
        "url": "/payments",
    }


def make_error(
    error_type: str,
    code: str | None = None,
    message: str = "An error occurred.",
) -> dict[str, Any]:
    err: dict[str, Any] = {"type": error_type, "message": message}
    if code is not None:
        err["code"] = code
    return {"error": err}


def sign_payload(body: str, secret: str, timestamp: int) -> str:
    """Produce a Kosovopay-Signature header value."""
    signed = f"{timestamp}.{body}"
    v1 = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={v1}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def respx_mock() -> Any:
    """Sync respx mock that intercepts all httpx calls."""
    with respx.mock(base_url=_BASE_URL, assert_all_called=False) as mock:
        yield mock


@pytest.fixture()
def client(respx_mock: Any) -> KosovoPay:  # noqa: F811 - shadowing is fine in fixtures
    """KosovoPay client wired to a respx mock transport."""
    return KosovoPay("sk_test_abc123")
