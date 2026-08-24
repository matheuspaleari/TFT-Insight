from __future__ import annotations

from typing import Any


def _comparisons(
    benchmark: dict[str, Any],
) -> list[dict[str, Any]]:
    return list(
        benchmark.get(
            "comparisons",
            [],
        )
    )


def build_kpi_explanations(
    *,
    analysis: dict[str, Any],
    benchmark: dict[str, Any],
    matches_analyzed: int,
) -> dict[str, Any]:
    prediction = analysis.get(
        "prediction",
        {},
    )
    coach = analysis.get(
        "coach",
        {},
    )
    signals = analysis.get(
        "signals",
        {},
    )
    comparisons = _comparisons(
        benchmark
    )

    sorted_best = sorted(
        comparisons,
        key=lambda item: float(
            item.get(
                "percentile",
                0,
            )
        ),
        reverse=True,
    )

    sorted_worst = sorted(
        comparisons,
        key=lambda item: float(
            item.get(
                "percentile",
                0,
            )
        ),
    )

    benchmark_factors = []

    for item in sorted_best[:2]:
        benchmark_factors.append(
            {
                "label": item.get(
                    "label",
                    "Strength",
                ),
                "value": (
                    f"Percentil "
                    f"{float(item.get('percentile', 0)):.0f}"
                ),
                "tone": "positive",
            }
        )

    for item in sorted_worst[:2]:
        benchmark_factors.append(
            {
                "label": item.get(
                    "label",
                    "Gap",
                ),
                "value": (
                    f"Percentil "
                    f"{float(item.get('percentile', 0)):.0f}"
                ),
                "tone": "warning",
            }
        )

    score_factors = []

    if comparisons:
        for item in sorted_best[:2]:
            score_factors.append(
                {
                    "label": item.get(
                        "label",
                        "Signal",
                    ),
                    "value": (
                        f"Percentil "
                        f"{float(item.get('percentile', 0)):.0f}"
                    ),
                    "tone": "positive",
                }
            )

        for item in sorted_worst[:1]:
            score_factors.append(
                {
                    "label": item.get(
                        "label",
                        "Gap",
                    ),
                    "value": (
                        f"Percentil "
                        f"{float(item.get('percentile', 0)):.0f}"
                    ),
                    "tone": "warning",
                }
            )

    top4_factors = []

    win_condition = coach.get(
        "win_condition"
    )
    attention = coach.get(
        "pregame_attention"
    )

    if win_condition:
        top4_factors.append(
            {
                "label": "Win condition",
                "value": str(
                    win_condition
                ),
                "tone": "positive",
            }
        )

    if attention:
        top4_factors.append(
            {
                "label": "Ponto de atenção",
                "value": str(
                    attention
                ),
                "tone": "warning",
            }
        )

    confidence = prediction.get(
        "confidence"
    )

    confidence_factors = [
        {
            "label": "Partidas analisadas",
            "value": str(
                matches_analyzed
            ),
            "tone": (
                "positive"
                if matches_analyzed >= 20
                else "warning"
            ),
        }
    ]

    if isinstance(
        confidence,
        (int, float),
    ):
        confidence_factors.append(
            {
                "label": "Confiança do modelo",
                "value": (
                    f"{float(confidence):.1f}%"
                ),
                "tone": (
                    "positive"
                    if confidence >= 80
                    else "neutral"
                ),
            }
        )

    expected_factors = []

    for key, label in (
        (
            "tempo",
            "Tempo",
        ),
        (
            "economy",
            "Economia",
        ),
        (
            "contest_level",
            "Contestação",
        ),
    ):
        value = signals.get(
            key
        )

        if value not in (
            None,
            "",
        ):
            expected_factors.append(
                {
                    "label": label,
                    "value": str(
                        value
                    ),
                    "tone": (
                        "warning"
                        if key
                        == "contest_level"
                        else "neutral"
                    ),
                }
            )

    return {
        "score": {
            "title": "Por que este Score?",
            "body": (
                "O Score resume a leitura geral retornada pela Engine. "
                "Os fatores abaixo ajudam a contextualizar a nota com os "
                "sinais e percentis disponíveis, sem inventar pesos que "
                "o contrato atual não expõe."
            ),
            "factors": score_factors,
            "note": (
                "Os pesos matemáticos internos do Score não são "
                "decompostos pelo contrato público atual."
            ),
        },
        "top4": {
            "title": "Por que esta probabilidade de Top 4?",
            "body": (
                "A probabilidade vem da previsão da Engine para o "
                "conjunto de partidas analisado. Abaixo mostramos o "
                "contexto público mais relevante associado à leitura."
            ),
            "factors": top4_factors,
            "note": (
                "Não exibimos contribuição artificial de features "
                "quando ela não existe no contrato."
            ),
        },
        "confidence": {
            "title": "Por que esta confiança?",
            "body": (
                "Confidence representa o quanto o modelo considera "
                "estável a previsão atual dentro da amostra analisada."
            ),
            "factors": confidence_factors,
            "note": (
                "A explicação usa apenas amostra e confiança "
                "efetivamente retornadas pela plataforma."
            ),
        },
        "benchmark": {
            "title": "Por que este Benchmark?",
            "body": (
                "O percentil compara o jogador com a distribuição "
                "Challenger usada como referência."
            ),
            "factors": benchmark_factors,
            "note": (
                "Percentis são calculados pelo Benchmark Intelligence "
                "contra os perfis Challenger disponíveis."
            ),
        },
        "expected": {
            "title": "Por que esta colocação esperada?",
            "body": (
                "Expected Placement é a colocação estimada pela "
                "Prediction Engine. Os sinais abaixo ajudam a dar "
                "contexto à previsão."
            ),
            "factors": expected_factors,
            "note": (
                "O contrato atual não fornece uma decomposição "
                "numérica completa por feature."
            ),
        },
    }
