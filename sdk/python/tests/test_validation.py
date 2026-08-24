import httpx
import pytest

from tft_insight import (
    ResponseValidationError,
    TFTInsightClient,
)


def test_invalid_response() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={"invalid": True},
        )

    with TFTInsightClient(
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(
            ResponseValidationError
        ):
            client.health()
