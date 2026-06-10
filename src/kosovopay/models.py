"""Pydantic v2 DTOs for every object returned by the KosovoPay API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator

from kosovopay.enums import (
    BankCode,
    BankMode,
    CheckoutMode,
    CurrencyCode,
    PaymentStatus,
    RefundReason,
    RefundStatus,
    WebhookEventType,
)


def _coerce_enum(enum_cls: type, value: object) -> Any:
    """Return enum_cls.from_wire(value) when available, else enum_cls(value)."""
    if hasattr(enum_cls, "from_wire"):
        return enum_cls.from_wire(value)
    if isinstance(value, str):
        try:
            return enum_cls(value)
        except ValueError:
            return None
    return None


class KosovoPayModel(BaseModel):
    """Base model with shared config for all KosovoPay DTOs."""

    model_config = {"populate_by_name": True, "extra": "ignore"}


# ---------------------------------------------------------------------------
# Nested / small objects
# ---------------------------------------------------------------------------


class Payer(KosovoPayModel):
    name: str | None = None
    email: str | None = None


class Fx(KosovoPayModel):
    from_currency: CurrencyCode = Field(alias="from")
    to_currency: CurrencyCode = Field(alias="to")
    rate: str

    @model_validator(mode="before")
    @classmethod
    def _coerce_currencies(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in ("from", "to"):
                if key in data:
                    data[key] = CurrencyCode.from_wire(data[key])
        return data


class RefundCapability(KosovoPayModel):
    supported: bool = False
    partial: bool = False


class BankCapabilities(KosovoPayModel):
    currencies: list[CurrencyCode] = Field(default_factory=list)
    min_amount: int = 0
    amount_step: int = 1
    refunds: RefundCapability = Field(default_factory=RefundCapability)

    @model_validator(mode="before")
    @classmethod
    def _coerce_currencies(cls, data: Any) -> Any:
        if isinstance(data, dict) and "currencies" in data:
            data["currencies"] = [
                CurrencyCode.from_wire(c) for c in (data["currencies"] or [])
            ]
        return data


class Bank(KosovoPayModel):
    code: BankCode
    display_name: str = ""
    logo_url: str | None = None
    enabled: bool = False
    modes: list[BankMode] = Field(default_factory=list)
    capabilities: BankCapabilities = Field(default_factory=BankCapabilities)

    @model_validator(mode="before")
    @classmethod
    def _coerce_enums(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "code" in data:
                data["code"] = BankCode.from_wire(data["code"])
            if "modes" in data:
                data["modes"] = [BankMode.from_wire(m) for m in (data["modes"] or [])]
        return data


class Team(KosovoPayModel):
    id: str = ""
    name: str = ""
    logo_url: str | None = None


class Me(KosovoPayModel):
    team: Team = Field(default_factory=Team)
    mode: BankMode = BankMode.Test
    key_prefix: str = ""
    enabled_banks: list[BankCode] = Field(default_factory=list)
    default_currency: CurrencyCode | None = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_enums(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "mode" in data:
                data["mode"] = BankMode.from_wire(data["mode"])
            if "enabled_banks" in data:
                data["enabled_banks"] = [
                    BankCode.from_wire(b) for b in (data["enabled_banks"] or [])
                ]
            if "default_currency" in data and data["default_currency"] is not None:
                data["default_currency"] = CurrencyCode.from_wire(data["default_currency"])
        return data


class Currency(KosovoPayModel):
    code: CurrencyCode
    name: str | None = None
    symbol: str | None = None
    decimals: int = 2
    is_default: bool = False

    @model_validator(mode="before")
    @classmethod
    def _coerce_code(cls, data: Any) -> Any:
        if isinstance(data, dict) and "code" in data:
            data["code"] = CurrencyCode.from_wire(data["code"])
        return data


class Rate(KosovoPayModel):
    from_currency: CurrencyCode = Field(alias="from")
    to_currency: CurrencyCode = Field(alias="to")
    rate: str = "0"
    synced_at: str | None = None
    stale: bool = False

    @model_validator(mode="before")
    @classmethod
    def _coerce_currencies(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in ("from", "to"):
                if key in data:
                    data[key] = CurrencyCode.from_wire(data[key])
        return data


class Refund(KosovoPayModel):
    id: str = ""
    payment: str = ""
    amount: int = 0
    status: RefundStatus = RefundStatus.Pending
    reason: RefundReason | None = None
    failure_reason: str | None = None
    created: int | None = None
    succeeded_at: int | None = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_enums(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "status" in data:
                data["status"] = RefundStatus.from_wire(data["status"])
            if "reason" in data and data["reason"] is not None:
                try:
                    data["reason"] = RefundReason(data["reason"])
                except ValueError:
                    data["reason"] = None
        return data


class Payment(KosovoPayModel):
    id: str = ""
    status: PaymentStatus = PaymentStatus.Pending
    mode: BankMode = BankMode.Test
    amount: int = 0
    amount_captured: int = 0
    amount_refunded: int = 0
    currency: CurrencyCode = CurrencyCode.EUR
    bank_code: BankCode | None = None
    merchant_reference: str | None = None
    description: str | None = None
    payer: Payer | None = None
    line_items: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    fx: Fx | None = None
    last_error: str | None = None
    expires_at: int | None = None
    captured_at: int | None = None
    created: int = 0
    refunds: list[Refund] = Field(default_factory=list)
    checkout_mode: CheckoutMode | None = None
    hosted_url: str | None = None
    redirect_url: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_enums(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "status" in data:
                data["status"] = PaymentStatus.from_wire(data["status"])
            if "mode" in data:
                data["mode"] = BankMode.from_wire(data["mode"])
            if "currency" in data:
                data["currency"] = CurrencyCode.from_wire(data["currency"])
            if "bank_code" in data and data["bank_code"] is not None:
                data["bank_code"] = BankCode.from_wire(data["bank_code"])
            if "checkout_mode" in data and data["checkout_mode"] is not None:
                try:
                    data["checkout_mode"] = CheckoutMode(data["checkout_mode"])
                except ValueError:
                    data["checkout_mode"] = None
        return data


class WebhookEndpoint(KosovoPayModel):
    id: str = ""
    url: str = ""
    description: str | None = None
    enabled_events: list[WebhookEventType] = Field(default_factory=list)
    status: str = "enabled"
    mode: BankMode = BankMode.Test
    created: int | None = None
    secret: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_enums(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "mode" in data:
                data["mode"] = BankMode.from_wire(data["mode"])
            if "enabled_events" in data:
                data["enabled_events"] = [
                    WebhookEventType.from_wire(e) for e in (data["enabled_events"] or [])
                ]
        return data


class Event(KosovoPayModel):
    id: str = ""
    type: WebhookEventType = WebhookEventType.Unknown
    created: int = 0
    livemode: bool = False
    api_version: str = ""
    data: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _coerce_type(cls, data: Any) -> Any:
        if isinstance(data, dict) and "type" in data:
            data["type"] = WebhookEventType.from_wire(data["type"])
        return data

    @property
    def object(self) -> dict[str, Any]:
        obj = self.data.get("object")
        return obj if isinstance(obj, dict) else {}

    @property
    def previous_attributes(self) -> dict[str, Any] | None:
        prev = self.data.get("previous_attributes")
        return prev if isinstance(prev, dict) else None

    def as_payment(self) -> Payment:
        return Payment.model_validate(self.object)

    def as_refund(self) -> Refund:
        return Refund.model_validate(self.object)


class TimelineEvent(KosovoPayModel):
    type: str = ""
    at: int = 0


class DeletedResource(KosovoPayModel):
    id: str = ""
    deleted: bool = True


class AmountValidation(KosovoPayModel):
    valid: bool
    code: str | None = None
    message: str | None = None
    nearest_valid: list[int] | None = None


# ---------------------------------------------------------------------------
# List envelope
# ---------------------------------------------------------------------------


class ListEnvelope(KosovoPayModel):
    """A single-page list envelope: { object: "list", data, has_more, url }."""

    object: str = "list"
    data: list[dict[str, Any]] = Field(default_factory=list)
    has_more: bool = False
    url: str = ""
