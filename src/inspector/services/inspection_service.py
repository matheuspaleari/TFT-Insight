"""
Serviço responsável por explicar avaliações de Skills.
"""

from math import isfinite

from src.inspector.models import (
    MetricInspection,
    SkillInspection,
)
from src.learning.models import SkillAssessment
from src.performance_engine.models import (
    MetricEvaluation,
    MetricType,
    Performance,
)


INVERTED_METRICS = {
    MetricType.CONSISTENCY,
}


class InspectionService:
    """
    Converte os resultados técnicos dos Engines
    em diagnósticos explicáveis.
    """

    @classmethod
    def inspect_skill(
        cls,
        *,
        assessment: SkillAssessment,
        performance: Performance,
    ) -> SkillInspection:
        """
        Inspeciona uma única Skill.
        """

        evaluations_by_id = {
            evaluation.metric.value: evaluation
            for evaluation in performance.evaluations
        }

        metric_inspections = []

        for metric_id in (
            assessment.evidence_metric_ids
        ):
            evaluation = evaluations_by_id.get(
                metric_id
            )

            if evaluation is None:
                continue

            metric_inspections.append(
                cls._inspect_metric(
                    evaluation
                )
            )

        summary = cls._build_summary(
            assessment=assessment,
            inspections=tuple(
                metric_inspections
            ),
        )

        return SkillInspection(
            assessment=assessment,
            metric_inspections=tuple(
                metric_inspections
            ),
            summary=summary,
        )

    @classmethod
    def inspect_all(
        cls,
        *,
        assessments: tuple[
            SkillAssessment,
            ...,
        ],
        performance: Performance,
    ) -> tuple[SkillInspection, ...]:
        """
        Inspeciona todas as Skills avaliadas.
        """

        return tuple(
            cls.inspect_skill(
                assessment=assessment,
                performance=performance,
            )
            for assessment in assessments
        )

    @staticmethod
    def _inspect_metric(
        evaluation: MetricEvaluation,
    ) -> MetricInspection:
        benchmark = evaluation.benchmark_metric

        difference = (
            evaluation.player_value
            - benchmark.mean
        )

        standard_deviation = (
            benchmark.standard_deviation
        )

        if standard_deviation == 0:
            if difference == 0:
                raw_z_score = 0.0
            elif difference > 0:
                raw_z_score = float("inf")
            else:
                raw_z_score = float("-inf")
        else:
            raw_z_score = (
                difference
                / standard_deviation
            )

        higher_is_better = (
            evaluation.metric
            not in INVERTED_METRICS
        )

        interpreted_z_score = raw_z_score

        if not higher_is_better:
            interpreted_z_score *= -1

        if not isfinite(
            interpreted_z_score
        ):
            interpreted_z_score = (
                999.0
                if interpreted_z_score > 0
                else -999.0
            )

        return MetricInspection(
            metric=evaluation.metric,
            player_value=evaluation.player_value,
            benchmark_mean=benchmark.mean,
            benchmark_median=benchmark.median,
            benchmark_standard_deviation=(
                benchmark.standard_deviation
            ),
            benchmark_first_quartile=(
                benchmark.first_quartile
            ),
            benchmark_third_quartile=(
                benchmark.third_quartile
            ),
            benchmark_minimum=benchmark.minimum,
            benchmark_maximum=benchmark.maximum,
            difference_from_mean=round(
                difference,
                2,
            ),
            z_score=round(
                interpreted_z_score,
                2,
            ),
            percentile=round(
                evaluation.score,
                2,
            ),
            score=round(
                evaluation.score,
                2,
            ),
            weight=round(
                evaluation.weight,
                6,
            ),
            higher_is_better=(
                higher_is_better
            ),
        )

    @staticmethod
    def _build_summary(
        *,
        assessment: SkillAssessment,
        inspections: tuple[
            MetricInspection,
            ...,
        ],
    ) -> str:
        if not inspections:
            return (
                "Ainda não existem evidências diretas "
                "suficientes para explicar esta Skill."
            )

        if len(inspections) == 1:
            inspection = inspections[0]

            return (
                f"A avaliação de "
                f"{assessment.skill.title} utiliza "
                f"a métrica {inspection.metric_id}. "
                f"O resultado do jogador está "
                f"{inspection.position_label.lower()}."
            )

        weakest_metric = min(
            inspections,
            key=lambda item: item.percentile,
        )

        return (
            f"A avaliação de "
            f"{assessment.skill.title} utiliza "
            f"{len(inspections)} métricas. "
            f"A maior distância foi encontrada em "
            f"{weakest_metric.metric_id}, classificada como "
            f"{weakest_metric.position_label.lower()}."
        )