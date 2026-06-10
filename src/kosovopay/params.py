"""Parameter objects for mutating and filtering API calls."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from kosovopay.enums import (
    BankCode,
    CheckoutMode,
    CurrencyCode,
    PaymentStatus,
    RefundReason,
    WebhookEventType,
)


def _assert_url(url: str, field: str) -> None:
    scheme = urlparse(url).scheme.lower()
    if scheme not in ("http", "https"):
        raise ValueError(f"{field} must be an http or https URL.")


def _strip_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


class LineItem:
    """A single line item attached to a payment."""

    def __init__(
        self,
        name: str,
        quantity: int,
        unit_amount_cents: int,
        sku: str | None = None,
        image_url: str | None = None,
        variant: str | None = None,
    ) -> None:
        self.name = name
        self.quantity = quantity
        self.unit_amount_cents = unit_amount_cents
        self.sku = sku
        self.image_url = image_url
        self.variant = variant

    def to_dict(self) -> dict[str, Any]:
        return _strip_none(
            {
                "name": self.name,
                "quantity": self.quantity,
                "unit_amount_cents": self.unit_amount_cents,
                "sku": self.sku,
                "image_url": self.image_url,
                "variant": self.variant,
            }
        )


class CreatePaymentParams:
    """Parameters for creating a payment (hosted or direct)."""

    def __init__(
        self,
        amount: int,
        currency: CurrencyCode,
        success_url: str,
        mode: CheckoutMode = CheckoutMode.Hosted,
        bank_code: BankCode | None = None,
        cancel_url: str | None = None,
        fail_url: str | None = None,
        description: str | None = None,
        line_items: list[LineItem] | None = None,
        metadata: dict[str, Any] | None = None,
        expires_at: int | None = None,
        merchant_reference: str | None = None,
    ) -> None:
        if amount <= 0:
            raise ValueError("amount must be a positive integer in minor units.")
        if mode is CheckoutMode.Direct and bank_code is None:
            raise ValueError("bank_code is required for direct checkout mode.")
        if mode is CheckoutMode.Hosted and bank_code is not None:
            raise ValueError("bank_code must be omitted for hosted checkout mode.")
        _assert_url(success_url, "success_url")
        if cancel_url is not None:
            _assert_url(cancel_url, "cancel_url")
        if fail_url is not None:
            _assert_url(fail_url, "fail_url")

        self.amount = amount
        self.currency = currency
        self.success_url = success_url
        self.mode = mode
        self.bank_code = bank_code
        self.cancel_url = cancel_url
        self.fail_url = fail_url
        self.description = description
        self.line_items: list[LineItem] = line_items or []
        self.metadata: dict[str, Any] = metadata or {}
        self.expires_at = expires_at
        self.merchant_reference = merchant_reference

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "amount": self.amount,
            "currency": self.currency.value,
            "mode": self.mode.value,
            "success_url": self.success_url,
        }
        if self.bank_code is not None:
            d["bank_code"] = self.bank_code.value
        if self.cancel_url is not None:
            d["cancel_url"] = self.cancel_url
        if self.fail_url is not None:
            d["fail_url"] = self.fail_url
        if self.description is not None:
            d["description"] = self.description
        if self.line_items:
            d["line_items"] = [i.to_dict() for i in self.line_items]
        if self.metadata:
            d["metadata"] = self.metadata
        if self.expires_at is not None:
            d["expires_at"] = self.expires_at
        if self.merchant_reference is not None:
            d["merchant_reference"] = self.merchant_reference
        return d


class CreateRefundParams:
    """Parameters for creating a refund."""

    def __init__(
        self,
        payment: str,
        amount: int | None = None,
        reason: RefundReason | None = None,
    ) -> None:
        if not payment:
            raise ValueError("payment id is required.")
        if amount is not None and amount <= 0:
            raise ValueError(
                "amount, when given, must be a positive integer in minor units."
            )
        self.payment = payment
        self.amount = amount
        self.reason = reason

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"payment": self.payment}
        if self.amount is not None:
            d["amount"] = self.amount
        if self.reason is not None:
            d["reason"] = self.reason.value
        return d


class CreateWebhookEndpointParams:
    """Parameters for creating a webhook endpoint."""

    def __init__(
        self,
        url: str,
        enabled_events: list[WebhookEventType],
        description: str | None = None,
    ) -> None:
        if not enabled_events:
            raise ValueError("enabled_events must contain at least one event type.")
        _assert_url(url, "url")
        self.url = url
        self.enabled_events = enabled_events
        self.description = description

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "url": self.url,
            "enabled_events": [e.value for e in self.enabled_events],
        }
        if self.description is not None:
            d["description"] = self.description
        return d


class ListPaymentsParams:
    """Filter / pagination parameters for listing payments."""

    def __init__(
        self,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        status: PaymentStatus | None = None,
        bank_code: BankCode | None = None,
        currency: CurrencyCode | None = None,
        merchant_reference: str | None = None,
        created_gte: int | None = None,
        created_lte: int | None = None,
    ) -> None:
        self.limit = limit
        self.starting_after = starting_after
        self.ending_before = ending_before
        self.status = status
        self.bank_code = bank_code
        self.currency = currency
        self.merchant_reference = merchant_reference
        self.created_gte = created_gte
        self.created_lte = created_lte

    def to_query(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        if self.limit is not None:
            d["limit"] = self.limit
        if self.starting_after is not None:
            d["starting_after"] = self.starting_after
        if self.ending_before is not None:
            d["ending_before"] = self.ending_before
        if self.status is not None:
            d["status"] = self.status.value
        if self.bank_code is not None:
            d["bank_code"] = self.bank_code.value
        if self.currency is not None:
            d["currency"] = self.currency.value
        if self.merchant_reference is not None:
            d["merchant_reference"] = self.merchant_reference
        if self.created_gte is not None:
            d["created[gte]"] = self.created_gte
        if self.created_lte is not None:
            d["created[lte]"] = self.created_lte
        return d


class ListRefundsParams:
    """Filter / pagination parameters for listing refunds."""

    def __init__(
        self,
        payment: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
    ) -> None:
        self.payment = payment
        self.limit = limit
        self.starting_after = starting_after
        self.ending_before = ending_before

    def to_query(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        if self.payment is not None:
            d["payment"] = self.payment
        if self.limit is not None:
            d["limit"] = self.limit
        if self.starting_after is not None:
            d["starting_after"] = self.starting_after
        if self.ending_before is not None:
            d["ending_before"] = self.ending_before
        return d
