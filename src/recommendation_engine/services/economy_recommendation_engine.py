from src.decision_engine.models import (
    StrategicReport,
)

from src.recommendation_engine.models import (
    EconomyRecommendation,
)


class EconomyRecommendationEngine:
    @classmethod
    def recommend(
        cls,
        *,
        strategic_report: StrategicReport,
    ) -> EconomyRecommendation:
        report = strategic_report.economy

        if report.low_level_late_rate >= 25.0:
            action = (
                "Converta economia em nível ou força antes "
                "das partidas longas."
            )
            explanation = (
                "Há frequência relevante de partidas longas terminando "
                "em nível baixo."
            )
            confidence = 88.0

        elif report.level_8_rate < 60.0:
            action = (
                "Proteja mais economia para chegar ao nível 8."
            )
            explanation = (
                "A taxa de nível 8 ainda está abaixo do ideal."
            )
            confidence = 82.0

        elif (
            report.average_gold_left >= 25.0
            and report.level_9_rate < 30.0
        ):
            action = (
                "Gaste ou suba de nível antes de ser eliminado."
            )
            explanation = (
                "Existe ouro restante sem conversão proporcional "
                "em nível 9."
            )
            confidence = 84.0

        elif report.level_9_rate >= 40.0:
            action = (
                "Mantenha o padrão de Fast 8/Fast 9 quando o lobby permitir."
            )
            explanation = (
                "A progressão de nível é uma força do histórico."
            )
            confidence = 78.0

        else:
            action = (
                "Refine o timing entre estabilizar no nível 8 "
                "e avançar ao nível 9."
            )
            explanation = (
                "A economia é consistente, mas ainda há espaço "
                "para melhorar a conversão final."
            )
            confidence = 76.0

        return EconomyRecommendation(
            action=action,
            confidence=confidence,
            average_level=report.average_level,
            level_8_rate=report.level_8_rate,
            level_9_rate=report.level_9_rate,
            low_level_late_rate=(
                report.low_level_late_rate
            ),
            average_gold_left=report.average_gold_left,
            explanation=explanation,
            evidence=(
                f"Nível médio: {report.average_level:.2f}",
                f"Nível 8: {report.level_8_rate:.1f}%",
                f"Nível 9: {report.level_9_rate:.1f}%",
                (
                    "Ouro restante médio: "
                    f"{report.average_gold_left:.1f}"
                ),
            ),
        )
