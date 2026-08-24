from src.decision_engine.models import (
    FlexReport,
    StrategicReport,
)

from src.recommendation_engine.models import (
    PlaystyleProfile,
)


class PlaystyleRecommendationEngine:
    @classmethod
    def analyze(
        cls,
        *,
        strategic_report: StrategicReport,
        flex_report: FlexReport,
    ) -> PlaystyleProfile:
        economy = strategic_report.economy
        tempo = strategic_report.tempo

        fast_8 = min(
            100.0,
            economy.level_8_rate * 0.70
            + min(
                economy.average_level / 8.0,
                1.0,
            ) * 30.0,
        )

        fast_9 = min(
            100.0,
            economy.level_9_rate * 0.80
            + max(
                economy.average_level - 8.0,
                0.0,
            ) * 20.0,
        )

        reroll = max(
            0.0,
            100.0
            - economy.level_8_rate
            - economy.level_9_rate * 0.25,
        )

        flexible = flex_report.score

        aggressive = min(
            100.0,
            tempo.average_damage_to_players / 120.0 * 70.0
            + tempo.elimination_pressure_rate * 0.30,
        )

        scores = {
            "Fast 8": fast_8,
            "Fast 9": fast_9,
            "Reroll": reroll,
            "Flexível": flexible,
            "Agressivo": aggressive,
        }

        primary_style = max(
            scores,
            key=scores.get,
        )

        ordered = sorted(
            scores.values(),
            reverse=True,
        )

        confidence = min(
            100.0,
            55.0 + ordered[0] - ordered[1],
        )

        explanation = {
            "Fast 8": (
                "O padrão principal é chegar ao nível 8 com frequência "
                "e converter a economia nessa faixa."
            ),
            "Fast 9": (
                "O padrão principal é preservar recursos para alcançar "
                "o nível 9 com frequência."
            ),
            "Reroll": (
                "O padrão sugere permanência em níveis menores e foco "
                "em melhorar unidades antes do late game."
            ),
            "Flexível": (
                "O jogador alterna composições e carries com frequência."
            ),
            "Agressivo": (
                "O histórico mostra pressão elevada e dano consistente "
                "sobre o lobby."
            ),
        }[primary_style]

        return PlaystyleProfile(
            primary_style=primary_style,
            confidence=round(confidence, 2),
            fast_8_score=round(fast_8, 2),
            fast_9_score=round(fast_9, 2),
            reroll_score=round(reroll, 2),
            flexible_score=round(flexible, 2),
            aggressive_score=round(aggressive, 2),
            explanation=explanation,
            evidence=(
                f"Taxa nível 8: {economy.level_8_rate:.1f}%",
                f"Taxa nível 9: {economy.level_9_rate:.1f}%",
                f"Flexibilidade: {flex_report.score:.1f}",
                (
                    "Dano médio aos jogadores: "
                    f"{tempo.average_damage_to_players:.1f}"
                ),
            ),
        )
