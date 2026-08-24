from __future__ import annotations

from typing import Any


def build_executive_summary(
    *,
    analysis: dict[str, Any] | None = None,
    benchmark: dict[str, Any] | None = None,
) -> dict[str, Any]:
    analysis = analysis or {}
    benchmark = benchmark or {}

    prediction = analysis.get(
        "prediction",
        {},
    )
    coach = analysis.get(
        "coach",
        {},
    )

    comparisons = benchmark.get(
        "comparisons",
        [],
    )

    strongest = None
    weakest = None

    if comparisons:
        strongest = max(
            comparisons,
            key=lambda item: float(
                item.get(
                    "percentile",
                    0,
                )
            ),
        )
        weakest = min(
            comparisons,
            key=lambda item: float(
                item.get(
                    "percentile",
                    0,
                )
            ),
        )

    return {
        "overall_score": analysis.get(
            "overall_score"
        ),
        "classification": analysis.get(
            "classification",
            "Sem análise",
        ),
        "top4_probability": prediction.get(
            "top4_probability"
        ),
        "confidence": prediction.get(
            "confidence"
        ),
        "expected_placement": prediction.get(
            "expected_placement"
        ),
        "benchmark_percentile": benchmark.get(
            "overall_percentile"
        ),
        "benchmark_classification": benchmark.get(
            "classification"
        ),
        "strength": (
            strongest.get("label")
            if strongest
            else None
        ),
        "strength_percentile": (
            strongest.get("percentile")
            if strongest
            else None
        ),
        "opportunity": (
            weakest.get("label")
            if weakest
            else None
        ),
        "opportunity_percentile": (
            weakest.get("percentile")
            if weakest
            else None
        ),
        "attention": coach.get(
            "pregame_attention"
        ),
        "win_condition": coach.get(
            "win_condition"
        ),
    }
