from __future__ import annotations


class EconomyPlayerPresenter:
    """
    Contrato público do #27.
    Não recalcula analytics e não transforma estado final em decisão.
    """

    @classmethod
    def build(
        cls,
        report,
    ) -> dict:
        return {
            "summary": {
                "matches_analyzed": report.matches_analyzed,
                "score": report.score,
                "label": report.label,
                "average_level": report.average_level,
                "median_level": report.median_level,
                "average_gold_left": report.average_gold_left,
                "median_gold_left": report.median_gold_left,
                "average_last_round": report.average_last_round,
                "level_8_rate": report.level_8_rate,
                "level_9_rate": report.level_9_rate,
                "low_level_late_rate": report.low_level_late_rate,
            },
            "distribution": report.distribution.to_dict(),
            "placement_comparison": (
                report.placement_comparison.to_dict()
            ),
            "recent_trend": report.recent_trend.to_dict(),
            "latest": report.latest.to_dict(),
            "coach": cls._coach(report),
            "limitations": list(report.limitations),
        }

    @classmethod
    def _coach(
        cls,
        report,
    ) -> dict:
        trend = report.recent_trend
        comparison = report.placement_comparison

        observations = [
            (
                f"Você termina no nível 8 ou mais em "
                f"{report.level_8_rate:.1f}% das partidas e no nível 9 "
                f"ou mais em {report.level_9_rate:.1f}%."
            ),
            (
                f"Seu ouro restante médio é {report.average_gold_left:.1f}, "
                f"com mediana {report.median_gold_left:.1f}. "
                "Esse valor descreve o fim da partida; não indica sozinho "
                "se você gastou pouco ou demais."
            ),
        ]

        if trend.signal == "NIVEL_FINAL_MAIS_ALTO":
            observations.append(
                f"Nas {trend.recent_matches} partidas mais recentes, "
                f"o nível final médio subiu de "
                f"{trend.previous_average_level:.2f} para "
                f"{trend.recent_average_level:.2f}. "
                "Isso descreve progressão final, não prova melhora no timing."
            )
        elif trend.signal == "NIVEL_FINAL_MAIS_BAIXO":
            observations.append(
                f"Nas {trend.recent_matches} partidas mais recentes, "
                f"o nível final médio caiu de "
                f"{trend.previous_average_level:.2f} para "
                f"{trend.recent_average_level:.2f}. "
                "Isso não permite concluir se a causa foi roll, perda de vida, "
                "XP ou outra decisão."
            )
        elif trend.signal == "NIVEL_FINAL_ESTAVEL":
            observations.append(
                "O nível final médio permaneceu próximo entre os dois "
                "blocos recentes."
            )

        if (
            comparison.eligible_for_comparison
            and comparison.placement_delta is not None
        ):
            observations.append(
                "Há amostra suficiente para comparar partidas que terminaram "
                "no nível 9+ com as demais, mas essa diferença é apenas "
                "associação histórica e não uma recomendação automática de Fast 9."
            )
        else:
            observations.append(
                "Ainda não há amostra suficiente nos dois grupos para usar "
                "nível 9+ versus abaixo de 9 como comparação estável."
            )

        return {
            "headline": "Como sua economia termina nas partidas",
            "latest_reading": (
                f"Na partida mais recente você terminou no nível "
                f"{report.latest.level}, com {report.latest.gold_left} de ouro "
                f"restante, no round {report.latest.last_round}."
            ),
            "observations": observations,
            "next_match_principle": (
                "Planeje o próximo gasto grande antes de executá-lo: "
                "subir de nível, estabilizar ou preservar recursos são "
                "decisões diferentes."
            ),
            "guardrails": [
                "Ouro final não revela o timing de gasto.",
                "Nível final não revela quando a experiência foi comprada.",
                "O sistema não sabe quantos rolls foram feitos em cada estágio.",
                "Chegar ao nível 9 não é automaticamente melhor para todo lobby.",
            ],
        }
