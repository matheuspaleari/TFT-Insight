from tft_insight import TFTInsightClient


def main() -> None:
    with TFTInsightClient(
        base_url="http://127.0.0.1:8000",
        api_key="development",
    ) as client:
        report = client.analyze_player(
            game_name="Pinador doss",
            tag_line="000",
            match_count=20,
            learn=True,
        )

    print(
        "Score:",
        report.analysis.overall_score,
    )
    print(
        "Top 4:",
        report.analysis.prediction.top4_probability,
    )
    print(
        "Coach:",
        report.analysis.coach.headline,
    )
    print(
        "Cache reutilizado:",
        report.cache.cached_matches_used,
    )


if __name__ == "__main__":
    main()
