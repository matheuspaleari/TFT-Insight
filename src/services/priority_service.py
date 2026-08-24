"""
Serviço responsável por identificar e ordenar oportunidades de melhoria.

Este módulo não calcula métricas de jogador e não acessa a Riot API.
Ele utiliza exclusivamente as avaliações produzidas pelo
PerformanceCalculator.
"""

from src.performance_engine.constants import get_metric_metadata
from src.performance_engine.models import (
    MetricEvaluation,
    Performance,
    Priority,
)


class PriorityService:
    """
    Converte avaliações individuais em prioridades de evolução.

    As prioridades são ordenadas pelo impacto potencial que a melhoria
    daquela métrica pode gerar no score geral do jogador.
    """

    DEFAULT_PRIORITY_LIMIT = 3
    BENCHMARK_REFERENCE_SCORE = 50.0

    @classmethod
    def apply(
        cls,
        performance: Performance,
        limit: int = DEFAULT_PRIORITY_LIMIT,
    ) -> Performance:
        """
        Adiciona prioridades a um objeto Performance existente.

        Args:
            performance:
                Resultado produzido pelo PerformanceCalculator.

            limit:
                Quantidade máxima de prioridades geradas.

        Returns:
            O próprio objeto Performance, enriquecido com prioridades.
        """

        performance.priorities = cls.build(
            evaluations=performance.evaluations,
            limit=limit,
        )

        return performance

    @classmethod
    def build(
        cls,
        evaluations: list[MetricEvaluation],
        limit: int = DEFAULT_PRIORITY_LIMIT,
    ) -> list[Priority]:
        """
        Cria prioridades a partir das avaliações individuais.

        As prioridades são ordenadas pelo impacto potencial de melhoria.
        """

        if limit < 1:
            raise ValueError(
                "O limite de prioridades deve ser maior que zero."
            )

        if not evaluations:
            return []

        ordered_evaluations = sorted(
            evaluations,
            key=cls._calculate_impact,
            reverse=True,
        )

        selected_evaluations = ordered_evaluations[:limit]

        return [
            cls._build_priority(
                evaluation=evaluation,
                rank=rank,
            )
            for rank, evaluation in enumerate(
                selected_evaluations,
                start=1,
            )
        ]

    @staticmethod
    def _calculate_impact(
        evaluation: MetricEvaluation,
    ) -> float:
        """
        Estima o impacto potencial que melhorar esta métrica
        pode produzir no score geral.

        Quanto menor o score e maior o peso da métrica,
        maior será seu impacto.
        """

        improvement_potential = 100.0 - evaluation.score

        return improvement_potential * evaluation.weight

    @classmethod
    def _build_priority(
        cls,
        evaluation: MetricEvaluation,
        rank: int,
    ) -> Priority:
        """
        Converte uma MetricEvaluation em Priority.

        Os textos inseridos aqui são apenas metadados neutros.
        O RecommendationService será responsável por adaptar
        a comunicação ao nível geral do jogador.
        """

        metadata = get_metric_metadata(evaluation.metric)

        current_score = evaluation.score
        benchmark_score = cls.BENCHMARK_REFERENCE_SCORE

        gap = benchmark_score - current_score

        impact = cls._calculate_impact(evaluation)

        return Priority(
            id=evaluation.metric.value,
            title=metadata.title,
            description=metadata.description,
            current_score=current_score,
            benchmark_score=benchmark_score,
            gap=gap,
            impact=impact,
            confidence=100.0,
            rank=rank,
            recommendations=[],
        )