"""KosovoPay Python SDK.

Quick start::

    import kosovopay
    kp = kosovopay.KosovoPay("sk_test_…")
    payment = kp.payments.create(params)
"""

from __future__ import annotations

from kosovopay.amount_validator import validate_amount
from kosovopay.client import KosovoPay
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
from kosovopay.exceptions import (
    AmountBelowMinimumError,
    AmountStepInvalidError,
    ApiError,
    AuthenticationError,
    BankNotEnabledError,
    BankUnreachableError,
    IdempotencyError,
    KosovoPayError,
    PartialRefundUnsupportedError,
    PaymentError,
    PaymentNotCancelableError,
    PaymentNotRefundableError,
    PermissionError,
    RateLimitError,
    RefundExceedsRemainingError,
    ValidationError,
    WebhookSignatureError,
)
from kosovopay.models import (
    AmountValidation,
    Bank,
    BankCapabilities,
    Currency,
    DeletedResource,
    Event,
    Fx,
    ListEnvelope,
    Me,
    Payer,
    Payment,
    Rate,
    Refund,
    RefundCapability,
    Team,
    TimelineEvent,
    WebhookEndpoint,
)
from kosovopay.money import convert, format_amount, format_currency
from kosovopay.params import (
    CreatePaymentParams,
    CreateRefundParams,
    CreateWebhookEndpointParams,
    LineItem,
    ListPaymentsParams,
    ListRefundsParams,
)
from kosovopay.webhook import Webhook

__version__ = "1.0.0"

__all__ = [
    # Client
    "KosovoPay",
    # Webhook
    "Webhook",
    # Enums
    "BankCode",
    "BankMode",
    "CheckoutMode",
    "CurrencyCode",
    "PaymentStatus",
    "RefundReason",
    "RefundStatus",
    "WebhookEventType",
    # Models / DTOs
    "AmountValidation",
    "Bank",
    "BankCapabilities",
    "Currency",
    "DeletedResource",
    "Event",
    "Fx",
    "ListEnvelope",
    "Me",
    "Payment",
    "Payer",
    "Rate",
    "Refund",
    "RefundCapability",
    "Team",
    "TimelineEvent",
    "WebhookEndpoint",
    # Params
    "CreatePaymentParams",
    "CreateRefundParams",
    "CreateWebhookEndpointParams",
    "LineItem",
    "ListPaymentsParams",
    "ListRefundsParams",
    # Exceptions
    "KosovoPayError",
    "AuthenticationError",
    "PermissionError",
    "ValidationError",
    "IdempotencyError",
    "RateLimitError",
    "ApiError",
    "PaymentError",
    "AmountBelowMinimumError",
    "AmountStepInvalidError",
    "BankNotEnabledError",
    "BankUnreachableError",
    "PaymentNotCancelableError",
    "PaymentNotRefundableError",
    "RefundExceedsRemainingError",
    "PartialRefundUnsupportedError",
    "WebhookSignatureError",
    # Money helpers
    "format_amount",
    "format_currency",
    "convert",
    "validate_amount",
    # Version
    "__version__",
]
