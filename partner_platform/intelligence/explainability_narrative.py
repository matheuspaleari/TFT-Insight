from __future__ import annotations

from typing import Any


def _signal(
    signals: dict[str, Any],
    *names: str,
    fallback: str = "Não exposto pelo contrato",
) -> str:
    for name in names:
        value = signals.get(name)

        if value not in (
            None,
            "",
        ):
            return str(value)

    return fallback


def build_explainability_narrative(
    analysis: dict[str, Any],
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

    score = analysis.get(
        "overall_score"
    )
    confidence = prediction.get(
        "confidence"
    )

    evidence = [
        {
            "label": "Contestação",
            "value": _signal(
                signals,
                "contest_level",
                "carry_contested",
            ),
            "tone": "warning",
        },
        {
            "label": "Economia",
            "value": _signal(
                signals,
                "economy",
                "economy_state",
            ),
            "tone": "positive",
        },
        {
            "label": "Tempo",
            "value": _signal(
                signals,
                "tempo",
                "tempo_state",
            ),
            "tone": "neutral",
        },
    ]

    if (
        isinstance(confidence, (int, float))
        and confidence >= 80
    ):
        confidence_text = (
            "A Engine tem alta confiança nessa leitura."
        )
    elif isinstance(
        confidence,
        (int, float),
    ) and confidence >= 60:
        confidence_text = (
            "A leitura possui confiança moderada e deve ser "
            "combinada com o estado atual do lobby."
        )
    else:
        confidence_text = (
            "A confiança ainda é limitada; trate a recomendação "
            "como um ponto de atenção, não como uma regra fixa."
        )

    recommendation = (
        coach.get("priority")
        or coach.get("recommendation")
        or "Recomendação não exposta pelo contrato atual."
    )

    return {
        "score": score,
        "recommendation": str(
            recommendation
        ),
        "attention": str(
            coach.get(
                "pregame_attention",
                "Nenhum ponto de atenção específico foi retornado.",
            )
        ),
        "win_condition": str(
            coach.get(
                "win_condition",
                "Nenhuma condição de vitória específica foi retornada.",
            )
        ),
        "confidence_text": confidence_text,
        "evidence": evidence,
    }
