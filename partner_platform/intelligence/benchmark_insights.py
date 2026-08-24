from __future__ import annotations

from typing import Any


METRIC_LABELS = {
    "Top 4": "Taxa de Top 4",
    "Win rate": "Taxa de vitória",
    "Average placement": "Colocação média",
    "Average level": "Nível médio",
    "Damage": "Dano aos jogadores",
    "Consistency": "Consistência",
    "top4_rate": "Taxa de Top 4",
    "win_rate": "Taxa de vitória",
    "average_placement": "Colocação média",
    "average_level": "Nível médio",
    "average_damage_to_players": "Dano aos jogadores",
    "placement_standard_deviation": "Consistência",
}


def _metric_label(
    item: dict[str, Any],
) -> str:
    raw = str(
        item.get(
            "label",
            item.get(
                "metric",
                "Métrica",
            ),
        )
    )

    return METRIC_LABELS.get(
        raw,
        raw,
    )


def _score(
    item: dict[str, Any],
) -> float:
    percentile = item.get(
        "percentile"
    )

    if percentile is not None:
        return float(
            percentile
        )

    benchmark_mean = item.get(
        "benchmark_mean",
        item.get(
            "challenger_mean"
        ),
    )

    if benchmark_mean in (
        None,
        0,
    ):
        return float(
            item.get(
                "performance_delta",
                0.0,
            )
        )

    relative_gap = (
        float(
            item.get(
                "performance_delta",
                0.0,
            )
        )
        / abs(
            float(
                benchmark_mean
            )
        )
        * 100.0
    )

    return relative_gap


def _best_item(
    comparisons: list[
        dict[str, Any]
    ],
) -> dict[str, Any] | None:
    if not comparisons:
        return None

    return max(
        comparisons,
        key=_score,
    )


def _worst_item(
    comparisons: list[
        dict[str, Any]
    ],
) -> dict[str, Any] | None:
    if not comparisons:
        return None

    return min(
        comparisons,
        key=_score,
    )


def _comparison_sentence(
    item: dict[str, Any],
    *,
    benchmark_name: str,
) -> str:
    label = _metric_label(
        item
    )

    raw_percentile = item.get(
        "percentile"
    )

    if raw_percentile is None:
        benchmark_mean = item.get(
            "benchmark_mean",
            item.get(
                "challenger_mean",
            ),
        )
        performance_delta = float(
            item.get(
                "performance_delta",
                0.0,
            )
        )

        if benchmark_mean in (
            None,
            0,
        ):
            direction = (
                "acima"
                if performance_delta >= 0
                else "abaixo"
            )
            return (
                f"{label} está {direction} de {benchmark_name}."
            )

        relative_gap = (
            performance_delta
            / abs(
                float(
                    benchmark_mean
                )
            )
            * 100.0
        )

        if abs(
            relative_gap
        ) < 2:
            return (
                f"{label} está praticamente alinhada a "
                f"{benchmark_name} ({relative_gap:+.1f}%)."
            )

        if relative_gap > 0:
            return (
                f"{label} está {abs(relative_gap):.1f}% acima da "
                f"referência {benchmark_name}."
            )

        return (
            f"{label} está {abs(relative_gap):.1f}% abaixo da "
            f"referência {benchmark_name}."
        )

    percentile = float(
        raw_percentile
    )

    if percentile >= 75:
        return (
            f"{label} está no percentil {percentile:.0f} da "
            f"amostra {benchmark_name}, indicando um ponto forte claro."
        )

    if percentile >= 50:
        return (
            f"{label} está acima da mediana de {benchmark_name}, "
            f"no percentil {percentile:.0f}."
        )

    if percentile >= 25:
        return (
            f"{label} está abaixo da mediana de {benchmark_name}, "
            f"no percentil {percentile:.0f}."
        )

    return (
        f"{label} é atualmente o maior gap contra "
        f"{benchmark_name}, no percentil {percentile:.0f}."
    )


def build_benchmark_insights(
    comparison: dict[str, Any],
    *,
    benchmark_name: str = "benchmark selecionado",
) -> dict[str, Any]:
    comparisons = list(
        comparison.get(
            "comparisons",
            [],
        )
    )

    best = _best_item(
        comparisons
    )
    worst = _worst_item(
        comparisons
    )

    raw_overall = comparison.get(
        "overall_percentile"
    )
    overall = (
        float(
            raw_overall
        )
        if raw_overall
        is not None
        else None
    )

    if overall is None:
        above = sum(
            float(
                item.get(
                    "performance_delta",
                    0.0,
                )
            ) >= 0
            for item in comparisons
        )
        total = len(
            comparisons
        )

        if total == 0:
            headline = (
                "Ainda não há dados suficientes para comparar "
                f"o jogador com {benchmark_name}."
            )
        elif above == total:
            headline = (
                f"O jogador está na ou acima da referência "
                f"{benchmark_name} em todas as dimensões analisadas."
            )
        elif above >= total / 2:
            headline = (
                f"O jogador já está competitivo contra {benchmark_name}, "
                "mas ainda possui oportunidades específicas de evolução."
            )
        else:
            headline = (
                f"{benchmark_name} ainda está acima do jogador na maior "
                "parte das dimensões analisadas, indicando um caminho claro "
                "de progressão."
            )
    elif overall >= 75:
        headline = (
            f"O perfil está na faixa superior de {benchmark_name}, "
            f"com percentil geral P{overall:.0f}."
        )
    elif overall >= 50:
        headline = (
            f"O perfil está competitivo contra {benchmark_name}, "
            f"com percentil geral P{overall:.0f}, mas ainda possui "
            "gaps claros de evolução."
        )
    else:
        headline = (
            f"O benchmark {benchmark_name} mostra oportunidades "
            "relevantes antes de o jogador alcançar esse padrão."
        )

    return {
        "headline": headline,
        "strength": (
            _comparison_sentence(
                best,
                benchmark_name=benchmark_name,
            )
            if best
            else (
                "Ainda não há dados suficientes para identificar "
                "um ponto forte."
            )
        ),
        "opportunity": (
            _comparison_sentence(
                worst,
                benchmark_name=benchmark_name,
            )
            if worst
            else (
                "Ainda não há dados suficientes para identificar "
                "uma oportunidade."
            )
        ),
        "strength_metric": (
            _metric_label(
                best
            )
            if best
            else None
        ),
        "opportunity_metric": (
            _metric_label(
                worst
            )
            if worst
            else None
        ),
    }


def build_benchmark_recommendations(
    comparison: dict[str, Any],
    *,
    benchmark_name: str = "benchmark selecionado",
    limit: int = 3,
) -> list[dict[str, Any]]:
    comparisons = list(
        comparison.get(
            "comparisons",
            [],
        )
    )

    ranked = sorted(
        comparisons,
        key=_score,
    )

    recommendations: list[
        dict[str, Any]
    ] = []

    for item in ranked:
        if len(
            recommendations
        ) >= limit:
            break

        benchmark_mean = item.get(
            "benchmark_mean",
            item.get(
                "challenger_mean"
            ),
        )

        performance_delta = float(
            item.get(
                "performance_delta",
                0.0,
            )
        )

        if benchmark_mean in (
            None,
            0,
        ):
            relative_gap = performance_delta
        else:
            relative_gap = (
                performance_delta
                / abs(
                    float(
                        benchmark_mean
                    )
                )
                * 100.0
            )

        if relative_gap >= 0:
            continue

        magnitude = abs(
            relative_gap
        )

        if magnitude >= 20:
            priority = "critical"
        elif magnitude >= 10:
            priority = "high"
        elif magnitude >= 5:
            priority = "medium"
        else:
            priority = "low"

        recommendations.append(
            {
                "metric": _metric_label(
                    item
                ),
                "priority": priority,
                "relative_gap": relative_gap,
                "message": (
                    f"Reduzir o gap de {_metric_label(item)}: "
                    f"atualmente {magnitude:.1f}% abaixo de "
                    f"{benchmark_name}."
                ),
            }
        )

    return recommendations
