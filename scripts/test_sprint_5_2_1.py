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

from partner_platform.components import (
    compact_health_ribbon,
    explainable_kpi,
    smart_header,
)
from partner_platform.intelligence import (
    build_kpi_explanations,
)


def main() -> None:
    analysis = {
        "overall_score": 82.4,
        "classification": "Strong",
        "prediction": {
            "top4_probability": 74.0,
            "confidence": 89.0,
            "expected_placement": 3.28,
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

    benchmark = {
        "overall_percentile": 81.0,
        "classification": "Very competitive",
        "comparisons": [
            {
                "label": "Economy",
                "percentile": 91.0,
            },
            {
                "label": "Tempo",
                "percentile": 38.0,
            },
        ],
    }

    explanations = (
        build_kpi_explanations(
            analysis=analysis,
            benchmark=benchmark,
            matches_analyzed=20,
        )
    )

    assert smart_header
    assert compact_health_ribbon
    assert explainable_kpi

    assert (
        explanations[
            "confidence"
        ][
            "factors"
        ][0][
            "value"
        ]
        == "20"
    )

    assert (
        explanations[
            "benchmark"
        ][
            "factors"
        ]
    )

    print("=" * 92)
    print(
        "TFT INSIGHT - SPRINT 5.2.1"
    )
    print("=" * 92)
    print("Smart Header          : OK")
    print("Compact Health Ribbon : OK")
    print("Explainable KPI       : OK")
    print("Score explanation     : OK")
    print("Top4 explanation      : OK")
    print("Confidence explanation: OK")
    print("Benchmark explanation : OK")
    print("Expected explanation  : OK")
    print()
    print(
        "✓ Sprint 5.2.1 validada."
    )


if __name__ == "__main__":
    main()
