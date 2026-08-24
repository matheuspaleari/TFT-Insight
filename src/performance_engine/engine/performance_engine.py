"""
Orquestrador principal do Performance Engine.
"""

from src.performance_engine.calculators import (
    PerformanceCalculator,
)
from src.performance_engine.models import (
    Benchmark,
    MetricType,
    Performance,
    PlayerMetrics,
)
from src.services.priority_service import PriorityService
from src.services.recommendation_service import (
    RecommendationService,
)


class PerformanceEngine:
    """
    Coordena o cálculo completo da performance.
    """

    @classmethod
    def calculate(
        cls,
        *,
        player_metrics: PlayerMetrics,
        benchmark: Benchmark,
        performance_weights: dict[MetricType, float],
    ) -> Performance:
        """
        Calcula a análise utilizando o perfil
        competitivo selecionado.
        """

        performance = PerformanceCalculator.calculate(
            player_metrics=player_metrics,
            benchmark=benchmark,
            performance_weights=performance_weights,
        )

        performance = PriorityService.apply(
            performance
        )

        performance = RecommendationService.apply(
            performance
        )

        return performance