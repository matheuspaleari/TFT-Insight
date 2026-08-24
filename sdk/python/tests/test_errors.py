import httpx
import pytest

from tft_insight import (
    AuthenticationError,
    ContractCompatibilityError,
    TFTInsightClient,
)


def test_authentication_error() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            401,
            json={
                "detail": "API key inválida."
            },
        )

    with TFTInsightClient(
        transport=httpx.MockTransport(handler),
        max_retries=0,
    ) as client:
        with pytest.raises(
            AuthenticationError
        ):
            client.health()


def test_contract_compatibility(
    integrated_payload: dict,
) -> None:
    integrated_payload[
        "analysis"
    ][
        "meta"
    ][
        "contract_version"
    ] = "2.0.0"

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json=integrated_payload,
        )

    with TFTInsightClient(
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(
            ContractCompatibilityError
        ):
            client.analyze_player(
                game_name="Teste",
                tag_line="BR1",
            )
