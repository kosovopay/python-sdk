"""Tests that each resource hits the right HTTP method and path."""

from __future__ import annotations

import json
from typing import Any

import httpx

from kosovopay import KosovoPay
from tests.conftest import make_list, make_payment, make_refund

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _client() -> KosovoPay:
    return KosovoPay("sk_test_abc")


# ---------------------------------------------------------------------------
# /me
# ---------------------------------------------------------------------------


def test_me_hits_get_me(respx_mock: Any) -> None:
    respx_mock.get("/me").mock(
        return_value=httpx.Response(
            200,
            json={
                "team": {"id": "tm_1", "name": "Test Team", "logo_url": None},
                "mode": "test",
                "key_prefix": "sk_test",
                "enabled_banks": ["procredit"],
                "default_currency": "EUR",
            },
        )
    )
    kp = _client()
    me = kp.me()
    assert me.team.id == "tm_1"
    assert me.key_prefix == "sk_test"


# ---------------------------------------------------------------------------
# /banks
# ---------------------------------------------------------------------------


def test_banks_list_hits_get_banks(respx_mock: Any) -> None:
    bank_data = {
        "code": "procredit",
        "display_name": "ProCredit",
        "logo_url": None,
        "enabled": True,
        "modes": ["test", "live"],
        "capabilities": {
            "currencies": ["EUR"],
            "min_amount": 100,
            "amount_step": 1,
            "refunds": {"supported": True, "partial": True},
        },
    }
    respx_mock.get("/banks").mock(
        return_value=httpx.Response(200, json=make_list([bank_data]))
    )
    kp = _client()
    banks = kp.banks.list()
    assert len(banks) == 1
    assert banks[0].code.value == "procredit"
    assert banks[0].capabilities.refunds.partial is True


def test_banks_retrieve_hits_get_banks_code(respx_mock: Any) -> None:
    from kosovopay.enums import BankCode

    bank_data = {
        "code": "procredit",
        "display_name": "ProCredit",
        "logo_url": None,
        "enabled": True,
        "modes": ["test"],
        "capabilities": {
            "currencies": ["EUR"],
            "min_amount": 100,
            "amount_step": 1,
            "refunds": {"supported": True, "partial": False},
        },
    }
    route = respx_mock.get("/banks/procredit").mock(
        return_value=httpx.Response(200, json=bank_data)
    )
    kp = _client()
    bank = kp.banks.retrieve(BankCode.Procredit)
    assert bank.display_name == "ProCredit"
    assert route.called


# ---------------------------------------------------------------------------
# /currencies
# ---------------------------------------------------------------------------


def test_currencies_list_hits_get_currencies(respx_mock: Any) -> None:
    currency_data = {
        "code": "EUR",
        "name": "Euro",
        "symbol": "€",
        "decimals": 2,
        "is_default": True,
    }
    respx_mock.get("/currencies").mock(
        return_value=httpx.Response(200, json=make_list([currency_data]))
    )
    kp = _client()
    currencies = kp.currencies.list()
    assert len(currencies) == 1
    assert currencies[0].code.value == "EUR"
    assert currencies[0].is_default is True


# ---------------------------------------------------------------------------
# /rates
# ---------------------------------------------------------------------------


def test_rates_retrieve_hits_get_rates(respx_mock: Any) -> None:
    from kosovopay.enums import CurrencyCode

    route = respx_mock.get("/rates").mock(
        return_value=httpx.Response(
            200,
            json={
                "from": "EUR",
                "to": "USD",
                "rate": "1.0850",
                "synced_at": "2026-06-01T00:00:00Z",
                "stale": False,
            },
        )
    )
    kp = _client()
    rate = kp.rates.retrieve(CurrencyCode.EUR, CurrencyCode.USD)
    assert rate.rate == "1.0850"
    assert rate.stale is False
    assert route.called


# ---------------------------------------------------------------------------
# /payments
# ---------------------------------------------------------------------------


def test_payments_retrieve_hits_right_path(respx_mock: Any) -> None:
    route = respx_mock.get("/payments/pi_42").mock(
        return_value=httpx.Response(200, json=make_payment(id="pi_42"))
    )
    kp = _client()
    payment = kp.payments.retrieve("pi_42")
    assert payment.id == "pi_42"
    assert route.called


def test_payments_create_sends_post(respx_mock: Any) -> None:
    from kosovopay import CheckoutMode, CreatePaymentParams, CurrencyCode

    route = respx_mock.post("/payments").mock(
        return_value=httpx.Response(201, json=make_payment(id="pi_new", status="pending"))
    )
    kp = _client()
    params = CreatePaymentParams(
        amount=4990,
        currency=CurrencyCode.EUR,
        success_url="https://example.com/thanks",
        mode=CheckoutMode.Hosted,
    )
    payment = kp.payments.create(params)
    assert payment.id == "pi_new"
    assert route.called


def test_payments_create_sends_idempotency_key(respx_mock: Any) -> None:
    from kosovopay import CheckoutMode, CreatePaymentParams, CurrencyCode

    route = respx_mock.post("/payments").mock(
        return_value=httpx.Response(201, json=make_payment(id="pi_idem"))
    )
    kp = _client()
    params = CreatePaymentParams(
        amount=1000,
        currency=CurrencyCode.EUR,
        success_url="https://example.com/ok",
        mode=CheckoutMode.Hosted,
    )
    kp.payments.create(params, idempotency_key="custom-key-abc")
    assert route.called
    request = route.calls.last.request
    assert request.headers.get("Idempotency-Key") == "custom-key-abc"


def test_payments_create_auto_generates_idempotency_key(respx_mock: Any) -> None:
    """Without explicit key, an auto-generated UUID must still be present."""
    from kosovopay import CheckoutMode, CreatePaymentParams, CurrencyCode

    route = respx_mock.post("/payments").mock(
        return_value=httpx.Response(201, json=make_payment(id="pi_auto"))
    )
    kp = _client()
    params = CreatePaymentParams(
        amount=1000,
        currency=CurrencyCode.EUR,
        success_url="https://example.com/ok",
        mode=CheckoutMode.Hosted,
    )
    kp.payments.create(params)
    request = route.calls.last.request
    key = request.headers.get("Idempotency-Key")
    assert key is not None
    assert len(key) == 36  # UUID4 format


def test_payments_cancel_hits_cancel_endpoint(respx_mock: Any) -> None:
    route = respx_mock.post("/payments/pi_42/cancel").mock(
        return_value=httpx.Response(
            200, json=make_payment(id="pi_42", status="canceled", amount_captured=0)
        )
    )
    kp = _client()
    payment = kp.payments.cancel("pi_42", reason="duplicate")
    assert payment.status.value == "canceled"
    assert route.called


def test_payments_timeline_hits_timeline_endpoint(respx_mock: Any) -> None:
    route = respx_mock.get("/payments/pi_42/timeline").mock(
        return_value=httpx.Response(
            200,
            json=make_list(
                [
                    {"type": "payment.created", "at": 1749600000},
                    {"type": "payment.captured", "at": 1749600100},
                ]
            ),
        )
    )
    kp = _client()
    timeline = kp.payments.timeline("pi_42")
    assert len(timeline) == 2
    assert timeline[0].type == "payment.created"
    assert timeline[1].at == 1749600100
    assert route.called


# ---------------------------------------------------------------------------
# /refunds
# ---------------------------------------------------------------------------


def test_refunds_retrieve_hits_right_path(respx_mock: Any) -> None:
    route = respx_mock.get("/refunds/re_9").mock(
        return_value=httpx.Response(200, json=make_refund(id="re_9", status="pending"))
    )
    kp = _client()
    refund = kp.refunds.retrieve("re_9")
    assert refund.id == "re_9"
    assert refund.status.value == "pending"
    assert refund.reason is None
    assert route.called


def test_refunds_create_sends_post_and_idempotency_key(respx_mock: Any) -> None:
    from kosovopay import CreateRefundParams

    route = respx_mock.post("/refunds").mock(
        return_value=httpx.Response(201, json=make_refund(id="re_1"))
    )
    kp = _client()
    params = CreateRefundParams(payment="pi_1", amount=100)
    kp.refunds.create(params)
    assert route.called
    request = route.calls.last.request
    assert request.headers.get("Idempotency-Key") is not None
    body = json.loads(request.content)
    assert body["payment"] == "pi_1"
    assert body["amount"] == 100


# ---------------------------------------------------------------------------
# /webhook-endpoints
# ---------------------------------------------------------------------------


def test_webhook_endpoints_list(respx_mock: Any) -> None:
    we_data = {
        "id": "we_1",
        "url": "https://x/h",
        "description": None,
        "enabled_events": ["payment.captured"],
        "status": "enabled",
        "mode": "test",
        "created": 1,
        "secret": None,
    }
    respx_mock.get("/webhook-endpoints").mock(
        return_value=httpx.Response(200, json=make_list([we_data]))
    )
    kp = _client()
    endpoints = kp.webhook_endpoints.list()
    assert len(endpoints) == 1
    assert endpoints[0].id == "we_1"


def test_webhook_endpoints_rotate_secret(respx_mock: Any) -> None:
    route = respx_mock.post("/webhook-endpoints/we_1/rotate-secret").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "we_1",
                "url": "https://x/h",
                "description": None,
                "enabled_events": ["payment.captured"],
                "status": "enabled",
                "mode": "test",
                "created": 1,
                "secret": "whsec_new",
            },
        )
    )
    kp = _client()
    updated = kp.webhook_endpoints.rotate_secret("we_1")
    assert updated.secret == "whsec_new"
    assert route.called


def test_webhook_endpoints_delete(respx_mock: Any) -> None:
    route = respx_mock.delete("/webhook-endpoints/we_1").mock(
        return_value=httpx.Response(200, json={"id": "we_1", "deleted": True})
    )
    kp = _client()
    deleted = kp.webhook_endpoints.delete("we_1")
    assert deleted.deleted is True
    assert route.called
