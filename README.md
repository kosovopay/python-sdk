# KosovoPay Python SDK

Official Python client for the [KosovoPay](https://kosovo.sh) payment API.

## Installation

```bash
pip install kosovopay
```

Requires Python 3.10+ and no additional system dependencies. The SDK uses
[httpx](https://www.python-httpx.org/) for HTTP, [Pydantic v2](https://docs.pydantic.dev/)
for data parsing, and [tenacity](https://tenacity.readthedocs.io/) for retry logic.

## Quick start

```python
import kosovopay

kp = kosovopay.KosovoPay("sk_test_YOUR_KEY")
```

Use the client as a context manager to ensure the connection pool is closed:

```python
with kosovopay.KosovoPay("sk_test_YOUR_KEY") as kp:
    me = kp.me()
    print(me.team.name, me.mode)
```

---

## Hosted checkout

The simplest integration: KosovoPay renders a payment page and redirects the
customer on success.

```python
from kosovopay import KosovoPay, CreatePaymentParams, CurrencyCode, CheckoutMode

kp = KosovoPay("sk_test_YOUR_KEY")

params = CreatePaymentParams(
    amount=4990,                          # minor units (cents) — €49.90
    currency=CurrencyCode.EUR,
    success_url="https://example.com/thanks",
    cancel_url="https://example.com/cart",
    mode=CheckoutMode.Hosted,
    description="Order #1234",
)

payment = kp.payments.create(params)
print(payment.id)           # pi_…
print(payment.hosted_url)   # redirect the customer here
```

## Direct (bank-embedded) checkout

Bypass the hosted page and send the customer straight to their bank's UI.
Requires specifying the `bank_code`.

```python
from kosovopay import KosovoPay, CreatePaymentParams, CurrencyCode, CheckoutMode, BankCode

kp = KosovoPay("sk_test_YOUR_KEY")

params = CreatePaymentParams(
    amount=1500,
    currency=CurrencyCode.EUR,
    success_url="https://example.com/thanks",
    mode=CheckoutMode.Direct,
    bank_code=BankCode.Procredit,
)

payment = kp.payments.create(params)
print(payment.redirect_url)   # send the customer to this URL
```

## Retrieving a payment

```python
payment = kp.payments.retrieve("pi_abc123")
print(payment.status)         # PaymentStatus.Captured
print(payment.amount_captured)
```

## Cancelling a payment

```python
cancelled = kp.payments.cancel("pi_abc123", reason="customer request")
```

## Refunds

```python
from kosovopay import CreateRefundParams, RefundReason

params = CreateRefundParams(
    payment="pi_abc123",
    amount=500,                              # partial refund — €5.00
    reason=RefundReason.RequestedByCustomer,
)

refund = kp.refunds.create(params)
print(refund.id, refund.status)
```

To refund the full amount, omit `amount`:

```python
full_refund_params = CreateRefundParams(payment="pi_abc123")
refund = kp.refunds.create(full_refund_params)
```

## Cursor pagination

All `list()` methods return a **lazy generator** that transparently follows
cursor pages until `has_more` is false.

```python
from kosovopay import ListPaymentsParams, PaymentStatus

params = ListPaymentsParams(status=PaymentStatus.Captured, limit=50)

for payment in kp.payments.list(params):
    print(payment.id, payment.amount)
```

```python
for refund in kp.refunds.list():
    print(refund.id, refund.status)
```

## Webhooks

### Register an endpoint

```python
from kosovopay import CreateWebhookEndpointParams, WebhookEventType

we_params = CreateWebhookEndpointParams(
    url="https://example.com/webhooks/kosovopay",
    enabled_events=[
        WebhookEventType.PaymentCaptured,
        WebhookEventType.RefundSucceeded,
    ],
    description="Production webhook",
)

endpoint = kp.webhook_endpoints.create(we_params)
print(endpoint.secret)   # whsec_… — store this securely
```

### Verifying and consuming events

Always verify using the **raw request body bytes** (before any JSON decoding).
The `Webhook.construct_event` call returns a typed `Event` or raises
`WebhookSignatureError`.

```python
from kosovopay import Webhook, WebhookSignatureError

# In a Flask/Django/FastAPI view:
raw_body: str = request.body.decode("utf-8")   # or request.data
sig_header: str = request.headers["Kosovopay-Signature"]
secret: str = "whsec_…"                        # from endpoint.secret

try:
    event = Webhook.construct_event(raw_body, sig_header, secret)
except WebhookSignatureError as exc:
    print("Bad signature:", exc)
    return 400

if event.type.value == "payment.captured":
    payment = event.as_payment()
    print("Captured:", payment.id, payment.amount_captured)
elif event.type.value == "refund.succeeded":
    refund = event.as_refund()
    print("Refunded:", refund.id)
```

### Rotating a webhook secret

```python
updated = kp.webhook_endpoints.rotate_secret("we_abc123")
print(updated.secret)   # new secret — update your environment variable
```

---

## Error handling

Every network or API error raised by this SDK extends `KosovoPayError`.

```python
from kosovopay import (
    KosovoPayError,
    AuthenticationError,
    PermissionError,
    ValidationError,
    RateLimitError,
    PaymentError,
    AmountBelowMinimumError,
    BankNotEnabledError,
    ApiError,
)

try:
    payment = kp.payments.retrieve("pi_nonexistent")
except AuthenticationError:
    print("Invalid API key")
except PermissionError as exc:
    print("Not allowed:", exc.error_code)
except ValidationError as exc:
    print("Bad param:", exc.param)
except RateLimitError as exc:
    print(f"Rate limited — retry after {exc.retry_after}s")
except AmountBelowMinimumError as exc:
    print("Amount too small:", exc)
except PaymentError as exc:
    print("Payment error:", exc.error_code)
except ApiError as exc:
    print(f"Server error {exc.status_code}:", exc)
except KosovoPayError as exc:
    print("SDK error:", exc)
```

### Exception hierarchy

```
KosovoPayError
├── AuthenticationError          — invalid / missing API key (401)
├── PermissionError              — key lacks scope for this operation (403)
├── ValidationError              — invalid request parameters (422)
├── IdempotencyError             — idempotency key conflict
├── RateLimitError               — too many requests (429); has .retry_after
├── ApiError                     — unexpected server error (5xx)
├── WebhookSignatureError        — webhook HMAC verification failed
└── PaymentError                 — payment-domain errors
    ├── AmountBelowMinimumError  — amount < bank minimum
    ├── AmountStepInvalidError   — amount not a multiple of bank step
    ├── BankNotEnabledError      — bank not enabled on this key
    ├── BankUnreachableError     — bank temporarily unavailable
    ├── PaymentNotCancelableError
    ├── PaymentNotRefundableError
    ├── RefundExceedsRemainingError
    └── PartialRefundUnsupportedError
```

---

## Money helpers

Amounts are always **minor units** (e.g. 4990 = €49.90). The SDK ships
pure-integer money helpers with no float precision risk.

```python
from kosovopay import format_amount, format_currency, convert

# Format minor units
print(format_amount(4990, decimals=2, symbol="€"))   # "€49.90"
print(format_amount(500,  decimals=0, symbol="¥"))   # "¥500"
print(format_amount(-1250, decimals=2, symbol="$"))  # "-$12.50"

# Convert between currencies using a rate string
print(convert(10000, "1.12"))   # 11200

# Format using a Currency DTO from the API
currencies = kp.currencies.list()
eur = next(c for c in currencies if c.code.value == "EUR")
print(format_currency(4990, eur))   # "€49.90"
```

## Client-side amount validation

Pre-validate amounts without a round-trip to the server:

```python
from kosovopay import BankCode, CurrencyCode

result = kp.validate_amount(173, CurrencyCode.EUR, BankCode.Onefor)
if not result.valid:
    print(result.code)          # "amount_step_invalid"
    print(result.nearest_valid) # [150, 200]
```

---

## FX rates

```python
from kosovopay import CurrencyCode

rate = kp.rates.retrieve(CurrencyCode.EUR, CurrencyCode.USD)
print(rate.rate)       # "1.0850"
print(rate.stale)      # False
```

## Idempotency

Every `create` / `cancel` call automatically generates a UUID v4 idempotency
key. You can supply your own to safely retry from application code:

```python
import uuid

idem_key = str(uuid.uuid4())
payment = kp.payments.create(params, idempotency_key=idem_key)
# Retrying with the same key returns the original payment, never a duplicate.
payment_again = kp.payments.create(params, idempotency_key=idem_key)
assert payment.id == payment_again.id
```

---

## Configuration

```python
kp = KosovoPay(
    api_key="sk_live_…",
    base_url="https://api.kosovo.sh",   # default
    api_version="2026-06-01",           # default
    connect_timeout=10.0,               # seconds
    request_timeout=30.0,               # seconds
    max_retries=3,                      # network + 429 + 5xx are retried
)
```

## Typing

The package ships a `py.typed` marker file. All public APIs are fully type
annotated and compatible with mypy strict mode.

---

## License

**KosovoPay License 1.0** — free to use, including commercially, at no charge.
Modifying, forking, redistributing, or reverse-engineering the SDK is **not**
permitted; it is maintained solely by KosovoPay. See [LICENSE](LICENSE).
