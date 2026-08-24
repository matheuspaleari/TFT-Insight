from __future__ import annotations

from typing import Any


def _best_and_worst(
    benchmark: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    comparisons = list(
        benchmark.get(
            "comparisons",
            [],
        )
    )

    if not comparisons:
        return None, None

    best = max(
        comparisons,
        key=lambda item: float(
            item.get(
                "percentile",
                0,
            )
        ),
    )

    worst = min(
        comparisons,
        key=lambda item: float(
            item.get(
                "percentile",
                0,
            )
        ),
    )

    return best, worst


def build_executive_v2(
    *,
    analysis: dict[str, Any],
    benchmark: dict[str, Any],
) -> dict[str, Any]:
    prediction = analysis.get(
        "prediction",
        {},
    )
    coach = analysis.get(
        "coach",
        {},
    )

    best, worst = _best_and_worst(
        benchmark
    )

    overall_score = analysis.get(
        "overall_score"
    )
    overall_percentile = benchmark.get(
        "overall_percentile"
    )
    confidence = prediction.get(
        "confidence"
    )
    top4 = prediction.get(
        "top4_probability"
    )

    if isinstance(
        overall_percentile,
        (int, float),
    ):
        if overall_percentile >= 75:
            executive_reading = (
                "O jogador está em uma faixa competitiva alta contra "
                "o benchmark Challenger e já demonstra fundamentos "
                "consistentes para decisões avançadas."
            )
        elif overall_percentile >= 50:
            executive_reading = (
                "O jogador apresenta um perfil competitivo, com pontos "
                "fortes claros e algumas oportunidades objetivas de evolução."
            )
        else:
            executive_reading = (
                "O jogador ainda apresenta distância relevante para o "
                "benchmark Challenger, mas os gaps já estão bem identificados."
            )
    else:
        executive_reading = (
            "Ainda não há benchmark suficiente para gerar uma leitura "
            "executiva completa."
        )

    if isinstance(
        confidence,
        (int, float),
    ) and confidence >= 80:
        confidence_label = "High confidence"
    elif isinstance(
        confidence,
        (int, float),
    ) and confidence >= 60:
        confidence_label = "Moderate confidence"
    else:
        confidence_label = "Limited confidence"

    next_action = (
        coach.get("priority")
        or coach.get("recommendation")
        or coach.get("pregame_attention")
        or "Revisar a próxima partida com foco no principal gap."
    )

    return {
        "overall_score": overall_score,
        "classification": analysis.get(
            "classification",
            "Analysis",
        ),
        "top4_probability": top4,
        "confidence": confidence,
        "confidence_label": confidence_label,
        "expected_placement": prediction.get(
            "expected_placement"
        ),
        "benchmark_percentile": overall_percentile,
        "benchmark_classification": benchmark.get(
            "classification",
            "Challenger benchmark",
        ),
        "executive_reading": executive_reading,
        "strength": {
            "label": (
                best.get("label")
                if best
                else "Not available"
            ),
            "percentile": (
                best.get("percentile")
                if best
                else None
            ),
            "delta": (
                best.get("performance_delta")
                if best
                else None
            ),
        },
        "opportunity": {
            "label": (
                worst.get("label")
                if worst
                else "Not available"
            ),
            "percentile": (
                worst.get("percentile")
                if worst
                else None
            ),
            "delta": (
                worst.get("performance_delta")
                if worst
                else None
            ),
        },
        "next_action": str(
            next_action
        ),
        "attention": coach.get(
            "pregame_attention"
        ),
        "win_condition": coach.get(
            "win_condition"
        ),
    }
