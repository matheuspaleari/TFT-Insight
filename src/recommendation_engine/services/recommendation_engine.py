from src.decision_engine.models import (
    CompositionHistoryReport,
    ContestHistoryReport,
    FlexReport,
    StrategicReport,
)

from src.recommendation_engine.models import (
    RecommendationSuiteReport,
)

from .composition_recommendation_engine import (
    CompositionRecommendationEngine,
)
from .contest_recommendation_engine import (
    ContestRecommendationEngine,
)
from .economy_recommendation_engine import (
    EconomyRecommendationEngine,
)
from .improvement_priority_engine import (
    ImprovementPriorityEngine,
)
from .playstyle_recommendation_engine import (
    PlaystyleRecommendationEngine,
)


class RecommendationEngine:
    """
    Orquestra todos os motores alimentados pelo Priority Engine.
    """

    @classmethod
    def analyze(
        cls,
        *,
        strategic_report: StrategicReport,
        contest_history: ContestHistoryReport,
        flex_report: FlexReport,
        composition_history: CompositionHistoryReport,
    ) -> RecommendationSuiteReport:
        priorities = ImprovementPriorityEngine.analyze(
            strategic_report=strategic_report,
            contest_history=contest_history,
            flex_report=flex_report,
        )

        playstyle = PlaystyleRecommendationEngine.analyze(
            strategic_report=strategic_report,
            flex_report=flex_report,
        )

        contest = ContestRecommendationEngine.recommend(
            contest_history=contest_history,
        )

        economy = EconomyRecommendationEngine.recommend(
            strategic_report=strategic_report,
        )

        compositions = (
            CompositionRecommendationEngine.recommend(
                composition_history=composition_history,
            )
        )

        primary = priorities.primary_priority

        summary = (
            (
                f"Estilo principal: {playstyle.primary_style}. "
                f"Prioridade atual: {primary.category.value} — "
                f"{primary.title}."
            )
            if primary is not None
            else (
                f"Estilo principal: {playstyle.primary_style}. "
                "Nenhuma prioridade crítica foi identificada."
            )
        )

        return RecommendationSuiteReport(
            priorities=priorities,
            playstyle=playstyle,
            contest=contest,
            economy=economy,
            compositions=compositions,
            summary=summary,
        )
