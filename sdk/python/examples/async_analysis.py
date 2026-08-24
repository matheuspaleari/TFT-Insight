import asyncio

from tft_insight import AsyncTFTInsightClient


async def main() -> None:
    async with AsyncTFTInsightClient(
        base_url="http://127.0.0.1:8000",
        api_key="development",
    ) as client:
        health = await client.health()

        report = await client.analyze_player(
            game_name="Pinador doss",
            tag_line="000",
            match_count=20,
        )

    print(health.status)
    print(report.analysis.coach.summary)


if __name__ == "__main__":
    asyncio.run(main())
