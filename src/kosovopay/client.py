"""The top-level KosovoPay client."""

from __future__ import annotations

from kosovopay._http import _API_VERSION, _BASE_URL, HttpConnector
from kosovopay.amount_validator import validate_amount
from kosovopay.enums import BankCode, CurrencyCode
from kosovopay.models import AmountValidation, Me
from kosovopay.resources import (
    BanksResource,
    CurrenciesResource,
    MeResource,
    PaymentsResource,
    RatesResource,
    RefundsResource,
    WebhookEndpointsResource,
)

__all__ = ["KosovoPay"]


class KosovoPay:
    """The KosovoPay API client.

    Construct with a secret key, then reach resources via the typed accessors::

        kp = KosovoPay("sk_test_…")
        payment = kp.payments.create(params)
        me = kp.me()
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        api_key: str,
        base_url: str = _BASE_URL,
        api_version: str = _API_VERSION,
        connect_timeout: float = 10.0,
        request_timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self._connector = HttpConnector(
            api_key=api_key,
            base_url=base_url,
            api_version=api_version,
            connect_timeout=connect_timeout,
            request_timeout=request_timeout,
            max_retries=max_retries,
        )
        self._me_resource = MeResource(self._connector)
        self.banks = BanksResource(self._connector)
        self.currencies = CurrenciesResource(self._connector)
        self.rates = RatesResource(self._connector)
        self.payments = PaymentsResource(self._connector)
        self.refunds = RefundsResource(self._connector)
        self.webhook_endpoints = WebhookEndpointsResource(self._connector)

    def me(self) -> Me:
        """Identify the API key — its team, mode, and usable banks."""
        return self._me_resource.retrieve()

    def validate_amount(
        self, amount: int, currency: CurrencyCode, bank_code: BankCode
    ) -> AmountValidation:
        """Client-side amount pre-check against a bank's live capabilities.

        Catches ``amount_below_minimum`` / ``amount_step_invalid`` before a
        round-trip to the server.
        """
        bank = self.banks.retrieve(bank_code)
        return validate_amount(bank, amount, currency)

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._connector.close()

    def __enter__(self) -> KosovoPay:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
