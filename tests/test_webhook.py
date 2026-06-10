"""Tests for webhook signature verification and event construction."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest

from kosovopay import Webhook, WebhookSignatureError
from kosovopay.enums import WebhookEventType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sign(body: str, secret: str, timestamp: int) -> str:
    signed = f"{timestamp}.{body}"
    v1 = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={v1}"


_SECRET = "whsec_test_secret"
_NOW = 1_749_600_000  # fixed point in time for deterministic tests


def _event_body(payment_id: str = "pi_1") -> str:
    return json.dumps(
        {
            "id": "evt_1",
            "type": "payment.captured",
            "created": _NOW,
            "livemode": False,
            "api_version": "2026-06-01",
            "data": {
                "object": {
                    "object": "payment",
                    "id": payment_id,
                    "status": "captured",
                    "mode": "test",
                    "amount": 1500,
                    "amount_captured": 1500,
                    "amount_refunded": 0,
                    "currency": "EUR",
                    "created": _NOW,
                    "refunds": [],
                }
            },
        }
    )


# ---------------------------------------------------------------------------
# construct_event -- happy path
# ---------------------------------------------------------------------------


def test_construct_event_returns_typed_event() -> None:
    body = _event_body()
    header = _sign(body, _SECRET, _NOW)
    event = Webhook.construct_event(body, header, _SECRET, tolerance=300, now=_NOW)
    assert event.type is WebhookEventType.PaymentCaptured


def test_construct_event_as_payment_returns_payment() -> None:
    body = _event_body(payment_id="pi_42")
    header = _sign(body, _SECRET, _NOW)
    event = Webhook.construct_event(body, header, _SECRET, tolerance=300, now=_NOW)
    payment = event.as_payment()
    assert payment.id == "pi_42"
    assert payment.amount_captured == 1500


# ---------------------------------------------------------------------------
# verify -- good / bad cases
# ---------------------------------------------------------------------------


def test_verify_returns_true_for_valid_signature() -> None:
    body = '{"hello":"world"}'
    header = _sign(body, _SECRET, _NOW)
    assert Webhook.verify(body, header, _SECRET, now=_NOW) is True


def test_verify_returns_false_for_tampered_body() -> None:
    body = '{"hello":"world"}'
    header = _sign(body, _SECRET, _NOW)
    assert Webhook.verify(body + "x", header, _SECRET, now=_NOW) is False


def test_verify_returns_false_for_wrong_secret() -> None:
    body = '{"hello":"world"}'
    header = _sign(body, _SECRET, _NOW)
    assert Webhook.verify(body, header, "wrong_secret", now=_NOW) is False


def test_verify_returns_false_for_stale_timestamp() -> None:
    body = '{"hello":"world"}'
    header = _sign(body, _SECRET, _NOW)
    # advance clock by more than default 300s tolerance
    assert Webhook.verify(body, header, _SECRET, now=_NOW + 9999) is False


def test_verify_returns_false_for_malformed_header() -> None:
    body = '{"hello":"world"}'
    assert Webhook.verify(body, "garbage_header", _SECRET, now=_NOW) is False


def test_verify_returns_false_for_empty_header() -> None:
    body = '{"hello":"world"}'
    assert Webhook.verify(body, "", _SECRET, now=_NOW) is False


# ---------------------------------------------------------------------------
# construct_event -- error cases
# ---------------------------------------------------------------------------


def test_construct_event_raises_on_bad_signature() -> None:
    with pytest.raises(WebhookSignatureError):
        Webhook.construct_event('{"a":1}', "t=1,v1=bad", _SECRET, now=_NOW)


def test_construct_event_raises_on_stale_timestamp() -> None:
    body = '{"a":1}'
    header = _sign(body, _SECRET, _NOW)
    # now is far in the future, making _NOW look stale
    with pytest.raises(WebhookSignatureError):
        Webhook.construct_event(body, header, _SECRET, tolerance=300, now=_NOW + 9999)


def test_construct_event_raises_on_invalid_json() -> None:
    body = "not-json"
    ts = int(time.time())
    header = _sign(body, _SECRET, ts)
    with pytest.raises(WebhookSignatureError, match="not valid JSON"):
        Webhook.construct_event(body, header, _SECRET, tolerance=600, now=ts)
