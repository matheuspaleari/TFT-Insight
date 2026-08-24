import json

import httpx

from tft_insight import TFTInsightClient


def test_health() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.url.path == "/health"

        return httpx.Response(
            200,
            json={
                "status": "ok",
                "service": "TFT Insight API",
                "api_version": "1.0.0",
                "contract_version": "1.0.0",
                "environment": "test",
            },
        )

    client = TFTInsightClient(
        transport=httpx.MockTransport(handler),
    )

    response = client.health()

    assert response.status == "ok"

    client.close()


def test_analyze_player(
    integrated_payload: dict,
) -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert (
            request.url.path
            == "/v1/analyze/player"
        )

        body = json.loads(
            request.content.decode()
        )

        assert (
            body["player"]["game_name"]
            == "Pinador doss"
        )

        return httpx.Response(
            200,
            json=integrated_payload,
        )

    with TFTInsightClient(
        transport=httpx.MockTransport(handler),
    ) as client:
        response = client.analyze_player(
            game_name="Pinador doss",
            tag_line="000",
        )

    assert response.matches_analyzed == 20
    assert (
        response.analysis.prediction.top4_probability
        == 72.64
    )
