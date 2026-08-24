import httpx
import pytest

from tft_insight import AsyncTFTInsightClient


@pytest.mark.asyncio
async def test_async_analyze_player(
    integrated_payload: dict,
) -> None:
    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json=integrated_payload,
        )

    async with AsyncTFTInsightClient(
        transport=httpx.MockTransport(handler),
    ) as client:
        response = await client.analyze_player(
            game_name="Pinador doss",
            tag_line="000",
        )

    assert response.player_puuid == "puuid-test"
