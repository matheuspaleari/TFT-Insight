from __future__ import annotations

from typing import Any


def _clean_identifier(
    value: str | None,
) -> str:
    if not value:
        return ""

    cleaned = str(value)

    for prefix in (
        "TFT17_",
        "TFT16_",
        "TFT15_",
        "TFT14_",
        "TFT13_",
        "TFT12_",
        "TFT11_",
        "TFT_",
    ):
        if cleaned.startswith(prefix):
            cleaned = cleaned[
                len(prefix):
            ]
            break

    return cleaned.replace(
        "_",
        " ",
    ).strip()


def _message(
    *,
    role: str,
    metric: str,
    metric_label: str,
    title: str,
    message: str,
    evidence: dict[str, Any],
    priority: int | None = None,
    strategic_weight: int = 0,
) -> dict[str, Any]:
    return {
        "role": role,
        "metric": metric,
        "metric_label": metric_label,
        "title": title,
        "message": message,
        "priority": priority,
        "strategic_weight": strategic_weight,
        "evidence": evidence,
    }


def _composition_message(
    context: dict[str, Any],
) -> dict[str, Any] | None:
    if not context:
        return None

    diversity_rate = float(
        context.get(
            "diversity_rate",
            0.0,
        )
    )
    repetition_rate = float(
        context.get(
            "repetition_rate",
            0.0,
        )
    )
    usage_rate = float(
        context.get(
            "most_used_usage_rate",
            0.0,
        )
    )
    matches = int(
        context.get(
            "most_used_matches",
            0,
        )
    )
    carry = _clean_identifier(
        context.get(
            "most_used_carry_character_id"
        )
    )
    avg_placement = float(
        context.get(
            "most_used_average_placement",
            0.0,
        )
    )
    top4_rate = float(
        context.get(
            "most_used_top4_rate",
            0.0,
        )
    )
    forces = bool(
        context.get(
            "forces_composition",
            False,
        )
    )
    flexibility_label = str(
        context.get(
            "flexibility_label",
            "",
        )
    ).strip()
    flexibility_interpretation = str(
        context.get(
            "flexibility_interpretation",
            "",
        )
    ).strip()

    comp_reference = (
        f"uma linha centrada em {carry}"
        if carry
        else "a sua composição mais usada"
    )

    if forces:
        return _message(
            role="adjustment",
            metric="composition_pattern",
            metric_label="Padrão de composição",
            title=(
                "Existe concentração alta em uma mesma linha"
            ),
            message=(
                f"{comp_reference.capitalize()} aparece em "
                f"{usage_rate:.1f}% da amostra ({matches} partidas), "
                f"com repetição de {repetition_rate:.1f}%. "
                "O histórico mostra concentração elevada, mas isso não "
                "prova sozinho que você force a composição em todas as "
                "partidas. Vale acompanhar se essa preferência continua "
                "quando a linha fica menos favorável."
            ),
            priority=2,
            strategic_weight=80,
            evidence={
                "diversity_rate": diversity_rate,
                "usage_rate": usage_rate,
                "repetition_rate": repetition_rate,
                "matches": matches,
                "average_placement": avg_placement,
                "top4_rate": top4_rate,
                "carry": carry,
            },
        )

    if repetition_rate >= 35.0:
        return _message(
            role="adjustment",
            metric="composition_pattern",
            metric_label="Padrão de composição",
            title="Existe uma preferência clara de composição",
            message=(
                f"{comp_reference.capitalize()} aparece em "
                f"{usage_rate:.1f}% da amostra, e a repetição geral está "
                f"em {repetition_rate:.1f}%. Não é uma concentração "
                "extrema, mas já existe um padrão que vale acompanhar "
                "para que familiaridade não vire rigidez."
            ),
            priority=2,
            strategic_weight=65,
            evidence={
                "diversity_rate": diversity_rate,
                "usage_rate": usage_rate,
                "repetition_rate": repetition_rate,
                "matches": matches,
                "average_placement": avg_placement,
                "top4_rate": top4_rate,
                "carry": carry,
            },
        )

    return _message(
        role="strength",
        metric="composition_pattern",
        metric_label="Padrão de composição",
        title="Sua flexibilidade de composição é um ponto forte",
        message=(
            f"Você apresentou {diversity_rate:.1f}% de diversidade nas "
            f"composições analisadas, e a linha mais usada representa "
            f"apenas {usage_rate:.1f}% da amostra ({matches} partidas). "
            "O histórico não mostra concentração excessiva em uma única "
            "composição. "
            + (
                flexibility_interpretation
                if flexibility_interpretation
                else (
                    "Isso sustenta a leitura de que você já consegue "
                    "variar bem entre partidas."
                )
            )
        ),
        priority=None,
        strategic_weight=45,
        evidence={
            "diversity_rate": diversity_rate,
            "usage_rate": usage_rate,
            "repetition_rate": repetition_rate,
            "matches": matches,
            "average_placement": avg_placement,
            "top4_rate": top4_rate,
            "carry": carry,
            "flexibility_label": flexibility_label,
        },
    )


def _contest_message(
    context: dict[str, Any],
) -> dict[str, Any] | None:
    if not context:
        return None

    carry_rate = float(
        context.get(
            "carry_contest_rate",
            0.0,
        )
    )
    high_rate = float(
        context.get(
            "high_contest_rate",
            0.0,
        )
    )
    impact_raw = context.get(
        "placement_impact"
    )
    impact = (
        float(impact_raw)
        if impact_raw is not None
        else None
    )
    impact_label = str(
        context.get(
            "placement_impact_label",
            "",
        )
    ).strip()
    impact_interpretation = str(
        context.get(
            "placement_impact_interpretation",
            "",
        )
    ).strip()
    action = str(
        context.get(
            "action",
            "",
        )
    ).strip()
    explanation = str(
        context.get(
            "explanation",
            "",
        )
    ).strip()
    confidence = float(
        context.get(
            "confidence",
            0.0,
        )
    )

    most_contested = _clean_identifier(
        context.get(
            "most_contested_unit_id"
        )
    )
    latest_carry = _clean_identifier(
        context.get(
            "latest_carry_character_id"
        )
    )
    latest_contested = bool(
        context.get(
            "latest_carry_contested",
            False,
        )
    )
    latest_opponents = int(
        context.get(
            "latest_opponents_contesting_carry",
            0,
        )
    )

    contest_is_frequent = (
        carry_rate >= 45.0
        or high_rate >= 35.0
    )

    if contest_is_frequent:
        impact_text = (
            " " + impact_interpretation
            if impact_interpretation
            else ""
        )

        most_contested_text = (
            f" {most_contested} é a unidade que mais aparece "
            "contestada no histórico."
            if most_contested
            else ""
        )

        latest_text = ""

        if latest_carry:
            if latest_contested:
                latest_text = (
                    f" Na partida mais recente, {latest_carry} terminou "
                    f"contestado por {latest_opponents} adversário(s) "
                    "no board final."
                )
            else:
                latest_text = (
                    f" Na partida mais recente, {latest_carry} não "
                    "terminou contestado no board final."
                )

        body = (
            f"Seu carry aparece contestado em {carry_rate:.1f}% das "
            f"partidas, enquanto {high_rate:.1f}% da amostra termina "
            f"com contestação alta.{impact_text}{most_contested_text} "
            f"A recomendação do TFT Insight é: {action}. "
            f"{explanation}{latest_text}"
        )

        return _message(
            role="priority",
            metric="contest_pattern",
            metric_label="Contestação",
            title="Seu principal ponto de atenção é a contestação",
            message=body,
            priority=1,
            strategic_weight=100,
            evidence={
                "carry_contest_rate": carry_rate,
                "high_contest_rate": high_rate,
                "placement_impact": impact,
                "placement_impact_label": impact_label,
                "confidence": confidence,
                "most_contested_unit": most_contested,
                "latest_carry": latest_carry,
                "latest_carry_contested": latest_contested,
                "latest_opponents": latest_opponents,
            },
        )

    return _message(
        role="strength",
        metric="contest_pattern",
        metric_label="Contestação",
        title="Contestação não aparece como seu maior problema",
        message=(
            f"Seu carry aparece contestado em {carry_rate:.1f}% das "
            f"partidas, e a taxa de contestação alta é {high_rate:.1f}%. "
            "No histórico atual, esse padrão não aparece com frequência "
            "suficiente para ser tratado como prioridade principal."
        ),
        priority=None,
        strategic_weight=35,
        evidence={
            "carry_contest_rate": carry_rate,
            "high_contest_rate": high_rate,
            "placement_impact": impact,
            "confidence": confidence,
            "most_contested_unit": most_contested,
        },
    )


def _economy_message(
    context: dict[str, Any],
) -> dict[str, Any] | None:
    if not context:
        return None

    score = float(
        context.get(
            "score",
            0.0,
        )
    )
    label = str(
        context.get(
            "label",
            "",
        )
    ).strip()
    interpretation = str(
        context.get(
            "interpretation",
            "",
        )
    ).strip()

    gold = float(
        context.get(
            "average_gold_left",
            0.0,
        )
    )
    level = float(
        context.get(
            "average_level",
            0.0,
        )
    )
    level8 = float(
        context.get(
            "level_8_rate",
            0.0,
        )
    )
    level9 = float(
        context.get(
            "level_9_rate",
            0.0,
        )
    )
    low_level_late = float(
        context.get(
            "low_level_late_rate",
            0.0,
        )
    )
    action = str(
        context.get(
            "action",
            "",
        )
    ).strip()
    explanation = str(
        context.get(
            "explanation",
            "",
        )
    ).strip()
    confidence = float(
        context.get(
            "confidence",
            0.0,
        )
    )

    if (
        gold >= 25.0
        and level9 < 30.0
    ):
        return _message(
            role="adjustment",
            metric="economy_pattern",
            metric_label="Economia final",
            title="Existe espaço para converter melhor seus recursos finais",
            message=(
                f"Seu ouro restante médio é {gold:.1f}, enquanto a taxa "
                f"de nível 9 é {level9:.1f}%. O histórico sugere que "
                "algumas partidas terminam com recursos que poderiam ter "
                "sido convertidos antes da eliminação. "
                f"A recomendação atual é: {action} {explanation}"
            ),
            priority=2,
            strategic_weight=75,
            evidence={
                "score": score,
                "label": label,
                "average_gold_left": gold,
                "average_level": level,
                "level_8_rate": level8,
                "level_9_rate": level9,
                "low_level_late_rate": low_level_late,
                "confidence": confidence,
            },
        )

    if low_level_late >= 25.0:
        return _message(
            role="adjustment",
            metric="economy_pattern",
            metric_label="Economia final",
            title="Sua progressão final merece atenção",
            message=(
                f"Em {low_level_late:.1f}% da amostra, partidas longas "
                "terminam em nível 7 ou menos. Isso não permite afirmar "
                "quando gastar ou rolar, mas mostra que a conversão final "
                f"de recursos merece revisão. {action} {explanation}"
            ),
            priority=2,
            strategic_weight=70,
            evidence={
                "score": score,
                "label": label,
                "average_gold_left": gold,
                "average_level": level,
                "level_8_rate": level8,
                "level_9_rate": level9,
                "low_level_late_rate": low_level_late,
                "confidence": confidence,
            },
        )

    if level8 < 60.0:
        return _message(
            role="adjustment",
            metric="economy_pattern",
            metric_label="Economia final",
            title="Chegar ao nível 8 com mais frequência é um ponto de atenção",
            message=(
                f"Sua taxa de nível 8 é {level8:.1f}% e o nível médio "
                f"é {level:.2f}. O histórico mostra espaço para melhorar "
                f"a progressão final. {action} {explanation}"
            ),
            priority=2,
            strategic_weight=60,
            evidence={
                "score": score,
                "label": label,
                "average_gold_left": gold,
                "average_level": level,
                "level_8_rate": level8,
                "level_9_rate": level9,
                "low_level_late_rate": low_level_late,
                "confidence": confidence,
            },
        )

    return _message(
        role="strength",
        metric="economy_pattern",
        metric_label="Economia final",
        title="Sua progressão econômica é uma força do histórico",
        message=(
            f"O relatório econômico está classificado como {label or 'forte'}, "
            f"com score {score:.1f}. Você chega ao nível 8 em "
            f"{level8:.1f}% das partidas e ao nível 9 em {level9:.1f}%, "
            f"com nível médio de {level:.2f}. Seu ouro restante médio é "
            f"{gold:.1f}. "
            + (
                interpretation
                if interpretation
                else (
                    "Os dados sustentam manter esse padrão enquanto "
                    "você trabalha nos pontos que realmente aparecem "
                    "como prioridade."
                )
            )
        ),
        priority=None,
        strategic_weight=50,
        evidence={
            "score": score,
            "label": label,
            "average_gold_left": gold,
            "average_level": level,
            "level_8_rate": level8,
            "level_9_rate": level9,
            "low_level_late_rate": low_level_late,
            "confidence": confidence,
        },
    )


def build_strategic_coach_messages(
    coach_context: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """
    Converte o contexto determinístico já calculado pelos engines
    existentes em mensagens-base para o narrador local.

    Ordem:
      1. prioridades estratégicas;
      2. ajustes estratégicos;
      3. pontos fortes.

    Esta função não analisa JSON bruto e não usa IA.
    """
    if not coach_context:
        return []

    messages: list[
        dict[str, Any]
    ] = []

    for builder, key in (
        (_contest_message, "contest"),
        (_composition_message, "composition"),
        (_economy_message, "economy"),
    ):
        item = builder(
            coach_context.get(
                key,
                {},
            )
        )

        if item is not None:
            messages.append(
                item
            )

    role_order = {
        "priority": 0,
        "adjustment": 1,
        "strength": 2,
    }

    return sorted(
        messages,
        key=lambda item: (
            role_order.get(
                item.get(
                    "role",
                    "strength",
                ),
                9,
            ),
            -int(
                item.get(
                    "strategic_weight",
                    0,
                )
            ),
        ),
    )
