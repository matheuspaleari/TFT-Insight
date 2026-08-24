from src.decision_engine.models import (
    ContestHistoryReport,
)

from src.recommendation_engine.models import (
    ContestRecommendation,
)


class ContestRecommendationEngine:
    @classmethod
    def recommend(
        cls,
        *,
        contest_history: ContestHistoryReport,
    ) -> ContestRecommendation:
        impact = contest_history.placement_impact

        if (
            contest_history.carry_contest_rate >= 60.0
            and impact is not None
            and impact >= 1.0
        ):
            action = "Pivotar mais cedo"
            explanation = (
                "O carry é frequentemente contestado e o impacto "
                "observado na colocação é relevante."
            )
            confidence = 90.0

        elif contest_history.high_contest_rate >= 35.0:
            action = "Preparar composição alternativa"
            explanation = (
                "A composição entra em contestação alta com frequência."
            )
            confidence = 82.0

        elif contest_history.carry_contest_rate >= 45.0:
            action = "Monitorar o carry antes de comprometer recursos"
            explanation = (
                "A disputa direta pelo carry merece atenção, mesmo sem "
                "contestação extrema em todas as partidas."
            )
            confidence = 78.0

        else:
            action = "Manter a linha quando os itens estiverem corretos"
            explanation = (
                "A contestação não aparece como principal limitador."
            )
            confidence = 75.0

        return ContestRecommendation(
            action=action,
            confidence=confidence,
            carry_contest_rate=(
                contest_history.carry_contest_rate
            ),
            high_contest_rate=(
                contest_history.high_contest_rate
            ),
            placement_impact=impact,
            explanation=explanation,
            evidence=(
                (
                    "Contestação média: "
                    f"{contest_history.average_score:.1f}"
                ),
                (
                    "Carry contestado: "
                    f"{contest_history.carry_contest_rate:.1f}%"
                ),
                (
                    "Impacto observado: "
                    f"{impact:+.2f}"
                    if impact is not None
                    else "Impacto observado: indisponível"
                ),
            ),
        )
