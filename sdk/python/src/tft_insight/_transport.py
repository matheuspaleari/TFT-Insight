from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

import httpx

from .exceptions import (
    ConfigurationError,
    TransportError,
)
from ._errors import raise_for_api_error


_RETRYABLE_STATUS_CODES = {
    408,
    425,
    429,
    500,
    502,
    503,
    504,
}


@dataclass(slots=True, frozen=True)
class ClientOptions:
    base_url: str
    api_key: str | None
    timeout: float
    max_retries: int
    user_agent: str

    def __post_init__(self) -> None:
        if not self.base_url.strip():
            raise ConfigurationError(
                "base_url não pode ser vazio."
            )

        if self.timeout <= 0:
            raise ConfigurationError(
                "timeout deve ser maior que zero."
            )

        if self.max_retries < 0:
            raise ConfigurationError(
                "max_retries não pode ser negativo."
            )


def build_headers(
    options: ClientOptions,
    *,
    request_id: str | None = None,
) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": options.user_agent,
        "X-SDK-Contract-Major": "1",
    }

    if options.api_key:
        headers["X-API-Key"] = options.api_key

    if request_id:
        headers["X-Request-ID"] = request_id

    return headers


def request_with_retries(
    client: httpx.Client,
    *,
    method: str,
    url: str,
    options: ClientOptions,
    json_data: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> httpx.Response:
    attempts = options.max_retries + 1

    for attempt in range(attempts):
        try:
            response = client.request(
                method,
                url,
                json=json_data,
                headers=build_headers(
                    options,
                    request_id=request_id,
                ),
            )

        except (
            httpx.TimeoutException,
            httpx.NetworkError,
        ) as error:
            if attempt >= attempts - 1:
                raise TransportError(
                    "Falha de transporte ao chamar "
                    "a TFT Insight API."
                ) from error

            time.sleep(_retry_delay(attempt))
            continue

        if (
            response.status_code in _RETRYABLE_STATUS_CODES
            and attempt < attempts - 1
        ):
            time.sleep(_retry_delay(attempt))
            continue

        raise_for_api_error(response)
        return response

    raise TransportError(
        "Não foi possível concluir a requisição."
    )


async def async_request_with_retries(
    client: httpx.AsyncClient,
    *,
    method: str,
    url: str,
    options: ClientOptions,
    json_data: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> httpx.Response:
    import asyncio

    attempts = options.max_retries + 1

    for attempt in range(attempts):
        try:
            response = await client.request(
                method,
                url,
                json=json_data,
                headers=build_headers(
                    options,
                    request_id=request_id,
                ),
            )

        except (
            httpx.TimeoutException,
            httpx.NetworkError,
        ) as error:
            if attempt >= attempts - 1:
                raise TransportError(
                    "Falha de transporte ao chamar "
                    "a TFT Insight API."
                ) from error

            await asyncio.sleep(_retry_delay(attempt))
            continue

        if (
            response.status_code in _RETRYABLE_STATUS_CODES
            and attempt < attempts - 1
        ):
            await asyncio.sleep(_retry_delay(attempt))
            continue

        raise_for_api_error(response)
        return response

    raise TransportError(
        "Não foi possível concluir a requisição."
    )


def _retry_delay(attempt: int) -> float:
    return min(
        0.25 * (2 ** attempt),
        2.0,
    )
