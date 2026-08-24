from __future__ import annotations

class ContestPlayerPresenter:
    @classmethod
    def build(cls, report) -> dict:
        return {
            "summary": {
                "matches_analyzed": report.matches_analyzed,
                "average_score": report.average_score,
                "highest_score": report.highest_score,
                "level": report.level,
                "high_contest_rate": report.high_contest_rate,
                "carry_contest_rate": report.carry_contest_rate,
                "average_opponents_contesting_carry": report.average_opponents_contesting_carry,
                "average_opponents_with_shared_units": report.average_opponents_with_shared_units,
                "average_opponents_with_shared_traits": report.average_opponents_with_shared_traits,
            },
            "distribution": report.band_distribution.to_dict(),
            "placement_comparison": report.placement_comparison.to_dict(),
            "recurring_pressure": {
                "units": [x.to_dict() for x in report.most_contested_units],
                "traits": [x.to_dict() for x in report.most_contested_traits],
            },
            "latest": report.latest.to_dict(),
            "coach": cls._coach(report),
            "limitations": list(report.limitations),
        }

    @classmethod
    def _coach(cls, report) -> dict:
        placement = report.placement_comparison
        observations = [
            f"Seu carry aparece contestado em {report.carry_contest_rate:.1f}% das partidas analisadas.",
            f"Contestação alta ou extrema aparece em {report.high_contest_rate:.1f}% do histórico.",
        ]

        if placement.eligible_for_comparison and placement.placement_delta is not None:
            delta = placement.placement_delta
            if delta > 0:
                observations.append(
                    f"No histórico analisado, a colocação média foi {abs(delta):.2f} posição(ões) pior em partidas de alta contestação. Isso é associação, não prova que a contestação causou o resultado."
                )
            elif delta < 0:
                observations.append(
                    f"No histórico analisado, a colocação média foi {abs(delta):.2f} posição(ões) melhor em partidas de alta contestação. Isso mostra que contestação e resultado não devem ser tratados como causa automática."
                )
            else:
                observations.append(
                    "A colocação média foi semelhante entre partidas de alta e menor contestação."
                )
        else:
            observations.append(
                "Ainda não há amostra suficiente nos dois grupos para comparar colocação com segurança."
            )

        latest = report.latest
        if latest.carry_contested:
            latest_reading = (
                f"Na partida mais recente, o carry {latest.carry_character_id or 'identificado'} apareceu em "
                f"{latest.opponents_contesting_carry} adversário(s) no board final."
            )
        else:
            latest_reading = (
                "Na partida mais recente, o carry identificado não apareceu contestado diretamente nos boards finais adversários."
            )

        return {
            "headline": "Como a disputa aparece no seu histórico",
            "latest_reading": latest_reading,
            "observations": observations,
            "next_match_principle": (
                "Use a contestação como mais um sinal para decidir, sem abandonar automaticamente uma linha só porque ela está disputada."
            ),
            "guardrails": [
                "Contestação observada não prova que você fez scout.",
                "Contestação não é causa automática do resultado.",
                "Carry disputado não significa que pivotar era obrigatório.",
                "A análise descreve o board final, não toda a trajetória.",
            ],
        }
