from typing import Any

import httpx

from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    PlayerNotFoundError,
    RateLimitError,
    ServerError,
    TFTInsightAPIError,
    ValidationAPIError,
)
from .models import ErrorPayload


def raise_for_api_error(
    response: httpx.Response,
) -> None:
    if response.is_success:
        return

    payload = _parse_error_payload(response)

    message = (
        payload.message
        or _detail_to_message(payload.detail)
        or response.reason_phrase
        or "Erro retornado pela TFT Insight API."
    )

    kwargs: dict[str, Any] = {
        "status_code": response.status_code,
        "error_code": payload.error_code,
        "request_id": payload.request_id,
        "details": payload.details,
    }

    if response.status_code == 401:
        raise AuthenticationError(message, **kwargs)

    if response.status_code == 403:
        raise AuthorizationError(message, **kwargs)

    if response.status_code == 404:
        if (
            payload.error_code == "PLAYER_NOT_FOUND"
            or "jogador" in message.lower()
            or "player" in message.lower()
        ):
            raise PlayerNotFoundError(message, **kwargs)

        raise NotFoundError(message, **kwargs)

    if response.status_code == 422:
        raise ValidationAPIError(message, **kwargs)

    if response.status_code == 429:
        raise RateLimitError(message, **kwargs)

    if response.status_code >= 500:
        raise ServerError(message, **kwargs)

    raise TFTInsightAPIError(message, **kwargs)


def _parse_error_payload(
    response: httpx.Response,
) -> ErrorPayload:
    try:
        data = response.json()
    except ValueError:
        return ErrorPayload(
            message=response.text or None
        )

    if not isinstance(data, dict):
        return ErrorPayload(detail=data)

    return ErrorPayload.model_validate(data)


def _detail_to_message(detail: Any) -> str | None:
    if detail is None:
        return None

    if isinstance(detail, str):
        return detail

    if isinstance(detail, list):
        messages = []

        for item in detail:
            if isinstance(item, dict):
                message = item.get("msg")
                location = item.get("loc")

                if message:
                    if location:
                        messages.append(
                            f"{'.'.join(map(str, location))}: "
                            f"{message}"
                        )
                    else:
                        messages.append(str(message))
            else:
                messages.append(str(item))

        return "; ".join(messages) or None

    return str(detail)
