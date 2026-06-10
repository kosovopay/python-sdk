"""Webhook signature verification and event construction."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

from kosovopay.exceptions import WebhookSignatureError
from kosovopay.models import Event

_DEFAULT_TOLERANCE = 300  # seconds -- 5 minutes


class Webhook:
    """
    Verifies inbound webhook signatures and constructs a typed Event.

    Header: ``Kosovopay-Signature: t=<unix>,v1=<hex hmac-sha256>``
    Signed payload: ``"{t}.{raw_body}"`` -- always verify the *raw* body bytes,
    never a re-encoded copy.
    """

    SIGNATURE_HEADER = "Kosovopay-Signature"

    @staticmethod
    def construct_event(
        payload: str,
        signature_header: str,
        secret: str,
        tolerance: int = _DEFAULT_TOLERANCE,
        now: int | None = None,
    ) -> Event:
        """
        Verify the signature and decode the raw body into a typed :class:`Event`.

        Pass *now* (Unix seconds) for deterministic testing; omit to use wall clock.

        Raises :class:`~kosovopay.exceptions.WebhookSignatureError` on a
        missing / invalid / stale signature or unparseable body.
        """
        if not Webhook.verify(payload, signature_header, secret, now=now, tolerance=tolerance):
            raise WebhookSignatureError("Webhook signature verification failed.")
        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise WebhookSignatureError(
                f"Webhook payload is not valid JSON: {exc}"
            ) from exc
        return Event.model_validate(decoded)

    @staticmethod
    def verify(
        payload: str,
        signature_header: str,
        secret: str,
        now: int | None = None,
        tolerance: int = _DEFAULT_TOLERANCE,
    ) -> bool:
        """
        Constant-time HMAC-SHA256 check with a timestamp-tolerance replay window.

        Pass *now* for deterministic testing; omit to use the current wall clock.
        """
        parts = _parse_header(signature_header)
        t_str = parts.get("t", "")
        given = parts.get("v1", "")

        if not t_str or not given:
            return False

        try:
            timestamp = int(t_str)
        except ValueError:
            return False

        if timestamp <= 0:
            return False

        current = now if now is not None else int(time.time())
        if abs(current - timestamp) > tolerance:
            return False

        signed_payload = f"{timestamp}.{payload}"
        expected = hmac.new(
            secret.encode(), signed_payload.encode(), hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, given)


def _parse_header(header: str) -> dict[str, str]:
    """Parse ``t=123,v1=abc`` into ``{'t': '123', 'v1': 'abc'}``."""
    result: dict[str, str] = {}
    for piece in header.split(","):
        piece = piece.strip()
        if "=" in piece:
            k, _, v = piece.partition("=")
            result[k.strip()] = v.strip()
    return result
