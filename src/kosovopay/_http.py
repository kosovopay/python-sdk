"""HTTP connector built on httpx with retry logic via tenacity."""

from __future__ import annotations

import uuid
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from kosovopay.exceptions import KosovoPayError, RateLimitError, map_error

_SDK_VERSION = "1.0.0"
_API_VERSION = "2026-06-01"
_BASE_URL = "https://api.kosovo.sh"

# HTTP methods that are safe to retry without an idempotency key
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def _is_retryable(exc: BaseException) -> bool:
    """Return True for network errors, 429, and 5xx (key check done elsewhere)."""
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, KosovoPayError):
        if isinstance(exc, RateLimitError):
            return True
        if exc.status_code >= 500:
            return True
    return False


class _RetryState:
    """Carries per-request context into the tenacity retry predicate."""

    def __init__(self, method: str, idempotency_key: str | None) -> None:
        self.method = method.upper()
        self.idempotency_key = idempotency_key


def _build_retry_predicate(state: _RetryState) -> Any:
    """Return a tenacity retry predicate that respects safe-method / idempotency rules."""

    def predicate(exc: BaseException) -> bool:
        if isinstance(exc, httpx.TransportError):
            return True
        if isinstance(exc, KosovoPayError):
            if isinstance(exc, RateLimitError):
                return True
            if exc.status_code >= 500:
                is_safe = state.method in _SAFE_METHODS
                return is_safe or state.idempotency_key is not None
        return False

    return retry_if_exception(predicate)


class HttpConnector:
    """
    Thin httpx wrapper that handles:
    - Bearer auth
    - ``Kosovopay-Version`` + ``User-Agent`` headers
    - Timeouts
    - Automatic idempotency key generation for POST requests
    - Exponential-backoff retry via tenacity (network + 429 + 5xx)
    - Error envelope -> typed exception conversion
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = _BASE_URL,
        api_version: str = _API_VERSION,
        connect_timeout: float = 10.0,
        request_timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        if not api_key:
            raise ValueError("A KosovoPay API key is required.")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._api_version = api_version
        self._max_retries = max(1, max_retries)
        self._timeout = httpx.Timeout(request_timeout, connect=connect_timeout)
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers=self._default_headers(),
        )

    def _default_headers(self) -> dict[str, str]:
        import sys

        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Kosovopay-Version": self._api_version,
            "User-Agent": f"kosovopay-python/{_SDK_VERSION} (python/{py_ver})",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _raise_for_response(self, response: httpx.Response) -> None:
        if response.is_success:
            return
        retry_after_header = response.headers.get("Retry-After")
        retry_after: int | None = None
        if retry_after_header is not None and retry_after_header.isdigit():
            retry_after = int(retry_after_header)
        try:
            body = response.json()
        except Exception:
            body = {}
        raise map_error(body, response.status_code, retry_after)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> Any:
        """
        Execute an HTTP request with automatic retry.

        For POST requests an idempotency key is auto-generated (UUID4) if not
        supplied by the caller.  The same key is reused across all retry
        attempts so a retried create can never double-charge.
        """
        upper = method.upper()
        if upper == "POST" and idempotency_key is None:
            idempotency_key = str(uuid.uuid4())

        rs = _RetryState(upper, idempotency_key)
        predicate = _build_retry_predicate(rs)

        headers: dict[str, str] = {}
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key

        @retry(
            retry=predicate,
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=30),
            reraise=True,
        )
        def _do() -> Any:
            response = self._client.request(
                method=upper,
                url=path,
                params=params,
                json=json,
                headers=headers,
            )
            self._raise_for_response(response)
            return response.json()

        return _do()

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> Any:
        return self.request("POST", path, json=json, idempotency_key=idempotency_key)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HttpConnector:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Cursor pagination iterator
# ---------------------------------------------------------------------------


def paginate(
    connector: HttpConnector,
    path: str,
    params: dict[str, Any] | None = None,
) -> Any:
    """
    Generator that yields raw row dicts across all cursor pages.

    Pages forward with ``starting_after=<last id>`` until ``has_more`` is False.
    """
    query: dict[str, Any] = dict(params or {})

    while True:
        body = connector.get(path, params=query)
        if not isinstance(body, dict):
            break
        rows = body.get("data") or []
        if not isinstance(rows, list):
            break
        yield from rows
        has_more = body.get("has_more", False)
        if not has_more or not rows:
            break
        last = rows[-1]
        if isinstance(last, dict) and "id" in last:
            query = {**query, "starting_after": last["id"]}
            # Remove ending_before if present to avoid conflicts
            query.pop("ending_before", None)
        else:
            break


def _flatten_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
    """Flatten nested dicts like ``created={'gte': x}`` into ``created[gte]=x``."""
    if params is None:
        return None
    out: dict[str, Any] = {}
    for k, v in params.items():
        if isinstance(v, dict):
            for sub_k, sub_v in v.items():
                out[f"{k}[{sub_k}]"] = sub_v
        else:
            out[k] = v
    return out or None


def _strip_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _enum_value(v: Any) -> Any:
    """Return .value for enums, pass through everything else."""
    return v.value if hasattr(v, "value") else v
