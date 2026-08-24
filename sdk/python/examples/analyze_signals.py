from tft_insight import (
    AnalysisSignals,
    TFTInsightClient,
)


def main() -> None:
    signals = AnalysisSignals(
        economy_score=81.75,
        itemization_score=75.77,
        tempo_score=70.75,
        contest_score=52.79,
        flex_score=70.75,
        benchmark_score=68.0,
        sample_size=32,
        carry_contested=True,
        opponents_on_carry=1,
        average_placement=4.25,
    )

    with TFTInsightClient() as client:
        report = client.analyze_signals(
            signals=signals,
            patch="16.15",
            set_number=17,
        )

    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
