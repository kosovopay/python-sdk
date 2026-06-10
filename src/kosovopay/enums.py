"""Enumerations for the KosovoPay API.

Every enum that appears on the wire has a forward-compatible ``Unknown`` member
so that a server adding a new value never crashes an older SDK.  Use the
``from_wire`` class method instead of ``(value)`` to get this behaviour.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class _UnknownMixin:
    """Mixin that makes ``from_wire`` return ``cls.Unknown`` for unrecognised values."""

    @classmethod
    def from_wire(cls, value: object) -> Any:
        if not isinstance(value, str):
            return cls.Unknown  # type: ignore[attr-defined]
        try:
            return cls(value)  # type: ignore[call-arg]
        except ValueError:
            return cls.Unknown  # type: ignore[attr-defined]


class CheckoutMode(str, Enum):
    """How the payment is completed."""

    Hosted = "hosted"
    Direct = "direct"

    def requires_bank_code(self) -> bool:
        return self is CheckoutMode.Direct


class BankMode(str, _UnknownMixin, Enum):
    """Indicates whether a bank / key is in test or live mode."""

    Test = "test"
    Live = "live"
    Unknown = "unknown"


class BankCode(str, _UnknownMixin, Enum):
    """Machine-readable identifiers for supported banks."""

    Procredit = "procredit"
    Procard = "procard"
    Onefor = "onefor"
    Unknown = "unknown"


class PaymentStatus(str, _UnknownMixin, Enum):
    """Lifecycle state of a payment."""

    Pending = "pending"
    Authorized = "authorized"
    Captured = "captured"
    PartiallyRefunded = "partially_refunded"
    Refunded = "refunded"
    Failed = "failed"
    Canceled = "canceled"
    Unknown = "unknown"

    def is_terminal(self) -> bool:
        return self in (
            PaymentStatus.Captured,
            PaymentStatus.Refunded,
            PaymentStatus.Failed,
            PaymentStatus.Canceled,
        )


class RefundStatus(str, _UnknownMixin, Enum):
    """Lifecycle state of a refund."""

    Pending = "pending"
    Succeeded = "succeeded"
    Failed = "failed"
    Unknown = "unknown"


class RefundReason(str, Enum):
    """Reason for a refund."""

    RequestedByCustomer = "requested_by_customer"
    Duplicate = "duplicate"
    Fraudulent = "fraudulent"
    Other = "other"


class WebhookEventType(str, _UnknownMixin, Enum):
    """Types of events delivered to webhook endpoints."""

    PaymentCreated = "payment.created"
    PaymentCaptured = "payment.captured"
    PaymentFailed = "payment.failed"
    PaymentCanceled = "payment.canceled"
    PaymentExpired = "payment.expired"
    RefundSucceeded = "refund.succeeded"
    RefundFailed = "refund.failed"
    Unknown = "unknown"

    def is_refund(self) -> bool:
        return self in (WebhookEventType.RefundSucceeded, WebhookEventType.RefundFailed)


class CurrencyCode(str, _UnknownMixin, Enum):
    """Full ISO 4217 currency codes supported by KosovoPay."""

    AED = "AED"
    AFN = "AFN"
    ALL = "ALL"
    AMD = "AMD"
    ANG = "ANG"
    AOA = "AOA"
    ARS = "ARS"
    AUD = "AUD"
    AWG = "AWG"
    AZN = "AZN"
    BAM = "BAM"
    BBD = "BBD"
    BDT = "BDT"
    BGN = "BGN"
    BHD = "BHD"
    BIF = "BIF"
    BMD = "BMD"
    BND = "BND"
    BOB = "BOB"
    BRL = "BRL"
    BSD = "BSD"
    BTN = "BTN"
    BWP = "BWP"
    BYN = "BYN"
    BZD = "BZD"
    CAD = "CAD"
    CDF = "CDF"
    CHF = "CHF"
    CLP = "CLP"
    CNY = "CNY"
    COP = "COP"
    CRC = "CRC"
    CUP = "CUP"
    CVE = "CVE"
    CZK = "CZK"
    DJF = "DJF"
    DKK = "DKK"
    DOP = "DOP"
    DZD = "DZD"
    EGP = "EGP"
    ERN = "ERN"
    ETB = "ETB"
    EUR = "EUR"
    FJD = "FJD"
    FKP = "FKP"
    GBP = "GBP"
    GEL = "GEL"
    GHS = "GHS"
    GIP = "GIP"
    GMD = "GMD"
    GNF = "GNF"
    GTQ = "GTQ"
    GYD = "GYD"
    HKD = "HKD"
    HNL = "HNL"
    HTG = "HTG"
    HUF = "HUF"
    IDR = "IDR"
    ILS = "ILS"
    INR = "INR"
    IQD = "IQD"
    IRR = "IRR"
    ISK = "ISK"
    JMD = "JMD"
    JOD = "JOD"
    JPY = "JPY"
    KES = "KES"
    KGS = "KGS"
    KHR = "KHR"
    KMF = "KMF"
    KPW = "KPW"
    KRW = "KRW"
    KWD = "KWD"
    KYD = "KYD"
    KZT = "KZT"
    LAK = "LAK"
    LBP = "LBP"
    LKR = "LKR"
    LRD = "LRD"
    LSL = "LSL"
    LYD = "LYD"
    MAD = "MAD"
    MDL = "MDL"
    MGA = "MGA"
    MKD = "MKD"
    MMK = "MMK"
    MNT = "MNT"
    MOP = "MOP"
    MRU = "MRU"
    MUR = "MUR"
    MVR = "MVR"
    MWK = "MWK"
    MXN = "MXN"
    MYR = "MYR"
    MZN = "MZN"
    NAD = "NAD"
    NGN = "NGN"
    NIO = "NIO"
    NOK = "NOK"
    NPR = "NPR"
    NZD = "NZD"
    OMR = "OMR"
    PAB = "PAB"
    PEN = "PEN"
    PGK = "PGK"
    PHP = "PHP"
    PKR = "PKR"
    PLN = "PLN"
    PYG = "PYG"
    QAR = "QAR"
    RON = "RON"
    RSD = "RSD"
    RUB = "RUB"
    RWF = "RWF"
    SAR = "SAR"
    SBD = "SBD"
    SCR = "SCR"
    SDG = "SDG"
    SEK = "SEK"
    SGD = "SGD"
    SHP = "SHP"
    SLE = "SLE"
    SOS = "SOS"
    SRD = "SRD"
    SSP = "SSP"
    STN = "STN"
    SVC = "SVC"
    SYP = "SYP"
    SZL = "SZL"
    THB = "THB"
    TJS = "TJS"
    TMT = "TMT"
    TND = "TND"
    TOP = "TOP"
    TRY = "TRY"
    TTD = "TTD"
    TWD = "TWD"
    TZS = "TZS"
    UAH = "UAH"
    UGX = "UGX"
    USD = "USD"
    UYU = "UYU"
    UZS = "UZS"
    VES = "VES"
    VND = "VND"
    VUV = "VUV"
    WST = "WST"
    XAF = "XAF"
    XCD = "XCD"
    XOF = "XOF"
    XPF = "XPF"
    YER = "YER"
    ZAR = "ZAR"
    ZMW = "ZMW"
    ZWG = "ZWG"
    Unknown = "unknown"
