"""Typed exception hierarchy for the KosovoPay SDK.

Resolution order (mirrors the PHP ErrorMapper):
  1. Exact ``code`` match -> subclass
  2. ``type == rate_limit_error`` or HTTP 429 -> RateLimitError
  3. ``type`` family match -> subclass
  4. Fallback -> ApiError

An unrecognised code never crashes -- it falls back to its type family or ApiError.
"""

from __future__ import annotations

from typing import Any


class KosovoPayError(Exception):
    """Base for every error this SDK raises."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
        error_type: str | None = None,
        param: str | None = None,
        request_id: str | None = None,
        doc_url: str | None = None,
        status_code: int = 0,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.error_type = error_type
        self.param = param
        self.request_id = request_id
        self.doc_url = doc_url
        self.status_code = status_code


class AuthenticationError(KosovoPayError):
    """Invalid or missing API key."""


class PermissionError(KosovoPayError):
    """The API key does not have permission for this operation."""


class ValidationError(KosovoPayError):
    """One or more request parameters failed server-side validation."""


class IdempotencyError(KosovoPayError):
    """An idempotency constraint was violated."""


class RateLimitError(KosovoPayError):
    """Too many requests -- back off and retry."""

    def __init__(
        self,
        message: str,
        *,
        retry_after: int | None = None,
        error_code: str | None = None,
        error_type: str | None = None,
        param: str | None = None,
        request_id: str | None = None,
        doc_url: str | None = None,
        status_code: int = 429,
    ) -> None:
        super().__init__(
            message,
            error_code=error_code,
            error_type=error_type,
            param=param,
            request_id=request_id,
            doc_url=doc_url,
            status_code=status_code,
        )
        self.retry_after = retry_after


class ApiError(KosovoPayError):
    """An unexpected server-side error."""


class PaymentError(KosovoPayError):
    """A payment-domain error.  Subclasses carry specific codes."""


# Payment subcodes
class AmountBelowMinimumError(PaymentError):
    """The amount is below the bank's minimum."""


class AmountStepInvalidError(PaymentError):
    """The amount is not a valid multiple of the bank's step."""


class BankNotEnabledError(PaymentError):
    """The requested bank is not enabled on this key."""


class BankUnreachableError(PaymentError):
    """The bank is temporarily unreachable."""


class PaymentNotCancelableError(PaymentError):
    """The payment is in a state that cannot be cancelled."""


class PaymentNotRefundableError(PaymentError):
    """The payment cannot be refunded."""


class RefundExceedsRemainingError(PaymentError):
    """The refund amount exceeds the remaining refundable amount."""


class PartialRefundUnsupportedError(PaymentError):
    """The bank does not support partial refunds."""


class WebhookSignatureError(KosovoPayError):
    """Webhook signature verification failed."""


# ---------------------------------------------------------------------------
# Error mapper
# ---------------------------------------------------------------------------

_BY_CODE: dict[str, type[KosovoPayError]] = {
    "amount_below_minimum": AmountBelowMinimumError,
    "amount_step_invalid": AmountStepInvalidError,
    "bank_not_enabled": BankNotEnabledError,
    "bank_unreachable": BankUnreachableError,
    "payment_not_cancelable": PaymentNotCancelableError,
    "payment_not_refundable": PaymentNotRefundableError,
    "refund_exceeds_remaining": RefundExceedsRemainingError,
    "partial_refund_unsupported": PartialRefundUnsupportedError,
}

_BY_TYPE: dict[str, type[KosovoPayError]] = {
    "authentication_error": AuthenticationError,
    "permission_error": PermissionError,
    "validation_error": ValidationError,
    "idempotency_error": IdempotencyError,
    "payment_error": PaymentError,
    "api_error": ApiError,
}


def map_error(
    body: Any,
    status: int,
    retry_after: int | None = None,
) -> KosovoPayError:
    """Convert a decoded server error envelope to the matching exception type."""
    if not isinstance(body, dict):
        body = {}

    error: Any = body.get("error") or {}
    if not isinstance(error, dict):
        error = {}

    message: str = error.get("message") or "The request failed."
    code: str | None = error.get("code") or None
    err_type: str | None = error.get("type") or None
    param: str | None = error.get("param") or None
    request_id: str | None = error.get("request_id") or None
    doc_url: str | None = error.get("doc_url") or None

    common_kwargs: dict[str, Any] = {
        "error_code": code,
        "error_type": err_type,
        "param": param,
        "request_id": request_id,
        "doc_url": doc_url,
        "status_code": status,
    }

    # Rate-limit check first (type OR HTTP 429)
    if err_type == "rate_limit_error" or status == 429:
        return RateLimitError(message, retry_after=retry_after, **common_kwargs)

    # Exact code match
    if code is not None and code in _BY_CODE:
        return _BY_CODE[code](message, **common_kwargs)

    # Type-family match
    if err_type is not None and err_type in _BY_TYPE:
        return _BY_TYPE[err_type](message, **common_kwargs)

    return ApiError(message, **common_kwargs)
