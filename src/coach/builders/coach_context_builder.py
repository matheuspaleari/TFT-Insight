"""
Responsável por transformar uma Performance em CoachContext.
"""

from src.coach.models import (
    CoachContext,
    CoachMetric,
)
from src.performance_engine.constants import (
    get_metric_metadata,
)
from src.performance_engine.models import (
    MetricEvaluation,
    MetricType,
    Performance,
)


class CoachContextBuilder:
    """
    Constrói o contexto utilizado pelo Coach.

    Une informações de:

    - Performance
    - Priority
    - MetricEvaluation
    - MetricMetadata
    """

    @classmethod
    def build(
        cls,
        performance: Performance,
    ) -> CoachContext:

        metrics = tuple(
            cls._build_metric(
                performance=performance,
                evaluation=evaluation,
            )
            for evaluation in performance.evaluations
            if cls._has_priority(
                performance,
                evaluation.metric,
            )
        )

        return CoachContext(
            score=performance.score,
            status=performance.status,
            benchmark_name=performance.benchmark_name,
            matches_analyzed=performance.matches_analyzed,
            potential_score=performance.potential_score,
            metrics=metrics,
        )

    @staticmethod
    def _has_priority(
        performance: Performance,
        metric: MetricType,
    ) -> bool:

        return any(
            priority.id == metric.value
            for priority in performance.priorities
        )

    @classmethod
    def _build_metric(
        cls,
        *,
        performance: Performance,
        evaluation: MetricEvaluation,
    ) -> CoachMetric:

        priority = next(
            priority
            for priority in performance.priorities
            if priority.id == evaluation.metric.value
        )

        metadata = get_metric_metadata(
            evaluation.metric,
        )

        return CoachMetric(
            id=evaluation.metric.value,
            title=metadata.title,
            category=metadata.category.value,
            player_value=evaluation.player_value,
            benchmark_value=evaluation.benchmark_metric.mean,
            score=evaluation.score,
            weight=evaluation.weight,
            impact=priority.impact,
            description=metadata.description,
            drivers=metadata.drivers,
            recommendations=metadata.recommendations,
        )