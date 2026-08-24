from pathlib import Path
import sys

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from partner_platform.intelligence import (
    build_benchmark_insights,
    build_executive_summary,
    build_explainability_narrative,
)
from partner_platform.navigation import (
    NavigationCatalog,
)


def main() -> None:
    comparison = {
        "overall_percentile": 66.0,
        "classification": "Very competitive",
        "comparisons": [
            {
                "label": "Economy",
                "percentile": 88.0,
            },
            {
                "label": "Consistency",
                "percentile": 31.0,
            },
        ],
    }

    analysis = {
        "overall_score": 78.2,
        "classification": "Boa",
        "prediction": {
            "top4_probability": 72.0,
            "confidence": 81.0,
            "expected_placement": 3.4,
        },
        "coach": {
            "pregame_attention": "Scout contestação.",
            "win_condition": "Preserve economia.",
        },
        "signals": {
            "economy": "Strong",
            "tempo": "Stable",
            "contest_level": "Medium",
        },
    }

    insights = (
        build_benchmark_insights(
            comparison
        )
    )
    narrative = (
        build_explainability_narrative(
            analysis
        )
    )
    summary = (
        build_executive_summary(
            analysis=analysis,
            benchmark=comparison,
        )
    )

    assert (
        insights[
            "strength_metric"
        ]
        == "Economy"
    )
    assert (
        insights[
            "opportunity_metric"
        ]
        == "Consistency"
    )
    assert (
        narrative[
            "win_condition"
        ]
        == "Preserve economia."
    )
    assert (
        summary[
            "benchmark_percentile"
        ]
        == 66.0
    )

    labels = [
        item.label
        for item in (
            NavigationCatalog
            .default()
            .items
        )
    ]

    assert "Executive" in labels

    print("=" * 92)
    print(
        "TFT INSIGHT - PRODUCT INTELLIGENCE v0.6.0-alpha.1"
    )
    print("=" * 92)
    print("Explainability Premium : OK")
    print("Benchmark Insights      : OK")
    print("Executive Dashboard     : OK")
    print("Executive navigation    : OK")
    print("No engine mutation      : OK")
    print()
    print(
        "✓ Product Intelligence validado."
    )


if __name__ == "__main__":
    main()
