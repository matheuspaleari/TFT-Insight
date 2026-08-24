from __future__ import annotations

from typing import Any


def _best_item(
    comparisons: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not comparisons:
        return None

    return max(
        comparisons,
        key=lambda item: float(item.get("percentile") if item.get("percentile") is not None else (50.0 + item.get("performance_delta", 0.0))),
    )


def _worst_item(
    comparisons: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not comparisons:
        return None

    return min(
        comparisons,
        key=lambda item: float(item.get("percentile") if item.get("percentile") is not None else (50.0 + item.get("performance_delta", 0.0))),
    )


def _percentile_sentence(
    item: dict[str, Any],
) -> str:
    label = str(
        item.get("label", "Métrica")
    )
    raw_percentile = item.get("percentile")
    if raw_percentile is None:
        delta = float(item.get("performance_delta", 0.0))
        direction = "acima" if delta >= 0 else "abaixo"
        return f"{label} está {direction} da referência selecionada (Δ de performance {delta:+.2f})."
    percentile = float(raw_percentile)

    if percentile >= 75:
        return (
            f"{label} está acima de aproximadamente "
            f"{percentile:.0f}% dos perfis Challenger "
            "presentes no benchmark."
        )

    if percentile >= 50:
        return (
            f"{label} está acima da mediana Challenger, "
            f"no percentil {percentile:.0f}."
        )

    if percentile >= 25:
        return (
            f"{label} está abaixo da mediana Challenger, "
            f"no percentil {percentile:.0f}."
        )

    return (
        f"{label} é atualmente o maior gap em relação "
        f"ao benchmark, no percentil {percentile:.0f}."
    )


def build_benchmark_insights(
    comparison: dict[str, Any],
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

    raw_overall = comparison.get("overall_percentile")
    overall = float(raw_overall) if raw_overall is not None else None

    if overall is None:
        headline = "A comparação usa a referência competitiva selecionada e destaca os maiores deltas de desempenho."
    elif overall >= 75:
        headline = (
            "O perfil analisado já apresenta comportamento "
            "próximo da faixa superior do benchmark Challenger."
        )
    elif overall >= 50:
        headline = (
            "O perfil está competitivo contra a referência Challenger, "
            "mas ainda possui gaps claros de evolução."
        )
    else:
        headline = (
            "O benchmark mostra oportunidades relevantes antes de "
            "o perfil se aproximar do padrão Challenger."
        )

    return {
        "headline": headline,
        "strength": (
            _percentile_sentence(best)
            if best
            else "Ainda não há dados suficientes para identificar um ponto forte."
        ),
        "opportunity": (
            _percentile_sentence(worst)
            if worst
            else "Ainda não há dados suficientes para identificar uma oportunidade."
        ),
        "strength_metric": (
            best.get("label")
            if best
            else None
        ),
        "opportunity_metric": (
            worst.get("label")
            if worst
            else None
        ),
    }
