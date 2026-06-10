"""Resource classes that map to KosovoPay API endpoints."""

from __future__ import annotations

import builtins
from collections.abc import Generator
from typing import Any

from kosovopay._http import HttpConnector, paginate
from kosovopay.enums import BankCode, CurrencyCode
from kosovopay.models import (
    Bank,
    Currency,
    DeletedResource,
    ListEnvelope,
    Me,
    Payment,
    Rate,
    Refund,
    TimelineEvent,
    WebhookEndpoint,
)
from kosovopay.params import (
    CreatePaymentParams,
    CreateRefundParams,
    CreateWebhookEndpointParams,
    ListPaymentsParams,
    ListRefundsParams,
)


class MeResource:
    def __init__(self, connector: HttpConnector) -> None:
        self._c = connector

    def retrieve(self) -> Me:
        return Me.model_validate(self._c.get("/me"))


class BanksResource:
    def __init__(self, connector: HttpConnector) -> None:
        self._c = connector

    def list(self) -> builtins.list[Bank]:
        body = self._c.get("/banks")
        env = ListEnvelope.model_validate(body)
        return [Bank.model_validate(row) for row in env.data]

    def retrieve(self, code: BankCode) -> Bank:
        return Bank.model_validate(self._c.get(f"/banks/{code.value}"))


class CurrenciesResource:
    def __init__(self, connector: HttpConnector) -> None:
        self._c = connector

    def list(self) -> builtins.list[Currency]:
        body = self._c.get("/currencies")
        env = ListEnvelope.model_validate(body)
        return [Currency.model_validate(row) for row in env.data]


class RatesResource:
    def __init__(self, connector: HttpConnector) -> None:
        self._c = connector

    def retrieve(self, from_currency: CurrencyCode, to_currency: CurrencyCode) -> Rate:
        body = self._c.get(
            "/rates",
            params={"from": from_currency.value, "to": to_currency.value},
        )
        return Rate.model_validate(body)


class PaymentsResource:
    def __init__(self, connector: HttpConnector) -> None:
        self._c = connector

    def create(
        self,
        params: CreatePaymentParams,
        idempotency_key: str | None = None,
    ) -> Payment:
        return Payment.model_validate(
            self._c.post("/payments", json=params.to_dict(), idempotency_key=idempotency_key)
        )

    def retrieve(self, payment_id: str) -> Payment:
        return Payment.model_validate(self._c.get(f"/payments/{payment_id}"))

    def list(
        self, params: ListPaymentsParams | None = None
    ) -> Generator[Payment, None, None]:
        """Auto-paginating generator that yields every matching Payment."""
        query: dict[str, Any] = params.to_query() if params is not None else {}
        for row in paginate(self._c, "/payments", query):
            yield Payment.model_validate(row)

    def timeline(self, payment_id: str) -> builtins.list[TimelineEvent]:
        body = self._c.get(f"/payments/{payment_id}/timeline")
        env = ListEnvelope.model_validate(body)
        return [TimelineEvent.model_validate(row) for row in env.data]

    def cancel(
        self,
        payment_id: str,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> Payment:
        body: dict[str, Any] = {}
        if reason is not None:
            body["reason"] = reason
        return Payment.model_validate(
            self._c.post(
                f"/payments/{payment_id}/cancel",
                json=body,
                idempotency_key=idempotency_key,
            )
        )


class RefundsResource:
    def __init__(self, connector: HttpConnector) -> None:
        self._c = connector

    def create(
        self,
        params: CreateRefundParams,
        idempotency_key: str | None = None,
    ) -> Refund:
        return Refund.model_validate(
            self._c.post("/refunds", json=params.to_dict(), idempotency_key=idempotency_key)
        )

    def retrieve(self, refund_id: str) -> Refund:
        return Refund.model_validate(self._c.get(f"/refunds/{refund_id}"))

    def list(
        self, params: ListRefundsParams | None = None
    ) -> Generator[Refund, None, None]:
        """Auto-paginating generator that yields every matching Refund."""
        query: dict[str, Any] = params.to_query() if params is not None else {}
        for row in paginate(self._c, "/refunds", query):
            yield Refund.model_validate(row)


class WebhookEndpointsResource:
    def __init__(self, connector: HttpConnector) -> None:
        self._c = connector

    def create(
        self,
        params: CreateWebhookEndpointParams,
        idempotency_key: str | None = None,
    ) -> WebhookEndpoint:
        return WebhookEndpoint.model_validate(
            self._c.post(
                "/webhook-endpoints",
                json=params.to_dict(),
                idempotency_key=idempotency_key,
            )
        )

    def list(self) -> builtins.list[WebhookEndpoint]:
        body = self._c.get("/webhook-endpoints")
        env = ListEnvelope.model_validate(body)
        return [WebhookEndpoint.model_validate(row) for row in env.data]

    def delete(self, endpoint_id: str) -> DeletedResource:
        return DeletedResource.model_validate(
            self._c.delete(f"/webhook-endpoints/{endpoint_id}")
        )

    def rotate_secret(
        self,
        endpoint_id: str,
        idempotency_key: str | None = None,
    ) -> WebhookEndpoint:
        return WebhookEndpoint.model_validate(
            self._c.post(
                f"/webhook-endpoints/{endpoint_id}/rotate-secret",
                json={},
                idempotency_key=idempotency_key,
            )
        )
