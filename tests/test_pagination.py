"""Tests for cursor pagination across multiple pages."""

from __future__ import annotations

from typing import Any

import httpx

from kosovopay import KosovoPay
from tests.conftest import make_list, make_payment


def _client() -> KosovoPay:
    return KosovoPay("sk_test_abc")


def test_pagination_streams_across_two_pages_until_has_more_false(
    respx_mock: Any,
) -> None:
    """Paginator follows starting_after cursor until has_more is False."""
    page1 = make_list(
        [make_payment(id="pi_1"), make_payment(id="pi_2")],
        has_more=True,
    )
    page2 = make_list(
        [make_payment(id="pi_3")],
        has_more=False,
    )

    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(200, json=page1)
        return httpx.Response(200, json=page2)

    respx_mock.get("/payments").mock(side_effect=handler)

    kp = _client()
    ids = [p.id for p in kp.payments.list()]

    assert ids == ["pi_1", "pi_2", "pi_3"]
    assert call_count == 2


def test_pagination_second_request_carries_starting_after(respx_mock: Any) -> None:
    """The second page request must include starting_after=<last id of page 1>."""
    page1 = make_list(
        [make_payment(id="pi_1"), make_payment(id="pi_2")],
        has_more=True,
    )
    page2 = make_list([], has_more=False)

    requests_seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests_seen.append(request)
        if len(requests_seen) == 1:
            return httpx.Response(200, json=page1)
        return httpx.Response(200, json=page2)

    respx_mock.get("/payments").mock(side_effect=handler)

    kp = _client()
    list(kp.payments.list())  # exhaust the generator

    assert len(requests_seen) == 2
    second_url = str(requests_seen[1].url)
    assert "starting_after=pi_2" in second_url


def test_pagination_empty_first_page_yields_nothing(respx_mock: Any) -> None:
    respx_mock.get("/payments").mock(
        return_value=httpx.Response(200, json=make_list([], has_more=False))
    )
    kp = _client()
    result = list(kp.payments.list())
    assert result == []


def test_pagination_single_page_no_cursor(respx_mock: Any) -> None:
    """When has_more is False on page 1, only one request is made."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            200,
            json=make_list([make_payment(id="pi_only")], has_more=False),
        )

    respx_mock.get("/payments").mock(side_effect=handler)

    kp = _client()
    result = list(kp.payments.list())
    assert [p.id for p in result] == ["pi_only"]
    assert call_count == 1
