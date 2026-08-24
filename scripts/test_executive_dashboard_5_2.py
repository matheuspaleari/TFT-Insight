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
    build_executive_v2,
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
            "priority": "Preserve economy until Stage 4",
            "pregame_attention": "Scout early tempo.",
            "win_condition": "Reach level 9 with three carry items.",
        },
    }

    benchmark = {
        "overall_percentile": 81.0,
        "classification": "Very competitive",
        "comparisons": [
            {
                "label": "Economy",
                "percentile": 91.0,
                "performance_delta": 8.0,
            },
            {
                "label": "Tempo",
                "percentile": 38.0,
                "performance_delta": -5.0,
            },
        ],
    }

    result = build_executive_v2(
        analysis=analysis,
        benchmark=benchmark,
    )

    assert (
        result[
            "strength"
        ][
            "label"
        ]
        == "Economy"
    )

    assert (
        result[
            "opportunity"
        ][
            "label"
        ]
        == "Tempo"
    )

    assert (
        result[
            "confidence_label"
        ]
        == "High confidence"
    )

    assert (
        "Preserve economy"
        in result[
            "next_action"
        ]
    )

    print("=" * 92)
    print(
        "TFT INSIGHT - SPRINT 5.2 EXECUTIVE DASHBOARD 2.0"
    )
    print("=" * 92)
    print("Executive reading   : OK")
    print("Top strength        : OK")
    print("Top opportunity     : OK")
    print("Next action         : OK")
    print("Confidence label    : OK")
    print("Player Context      : REUSED")
    print()
    print(
        "✓ Sprint 5.2 Executive Dashboard 2.0 validada."
    )


if __name__ == "__main__":
    main()
