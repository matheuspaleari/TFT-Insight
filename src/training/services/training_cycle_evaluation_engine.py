from __future__ import annotations

from src.training.models.training_cycle_evaluation import (
    TrainingCycleEvaluation,
    TrainingMetricEvaluation,
)


class TrainingCycleEvaluationEngine:
    """
    Avalia mudança observada entre BEFORE e AFTER.

    Regras:
    - concluir a missão não significa melhorar;
    - SkillAssessment é contexto auxiliar;
    - só métricas relacionadas à missão decidem o resultado;
    - confiança da comparação é própria;
    - amostra AFTER pequena limita explicitamente a confiança;
    - nunca atribui causalidade ao exercício.
    """

    DEFAULT_RELATIVE_THRESHOLD = 0.05

    METRIC_DIRECTIONS: dict[str, int] = {
        "average_level": 1,
        "average_damage_to_players": 1,
        "average_players_eliminated": 1,
        "placement_standard_deviation": -1,
        "average_gold_left": 1,
    }

    @classmethod
    def evaluate(
        cls,
        *,
        before_metrics: dict[str, float | int | None],
        after_metrics: dict[str, float | int | None],
        before_coverage: float,
        after_coverage: float,
        before_sample_size: int,
        after_sample_size: int,
        relative_threshold: float = DEFAULT_RELATIVE_THRESHOLD,
    ) -> TrainingCycleEvaluation:
        metric_ids = tuple(
            dict.fromkeys(
                (
                    *before_metrics.keys(),
                    *after_metrics.keys(),
                )
            )
        )

        evaluations: list[TrainingMetricEvaluation] = []

        for metric_id in metric_ids:
            before = before_metrics.get(metric_id)
            after = after_metrics.get(metric_id)

            if not isinstance(before, (int, float)):
                continue

            if not isinstance(after, (int, float)):
                continue

            direction_rule = cls.METRIC_DIRECTIONS.get(metric_id)

            if direction_rule is None:
                continue

            before_value = float(before)
            after_value = float(after)
            delta = round(after_value - before_value, 4)

            if abs(before_value) < 1e-9:
                relative_change = None
                significance = "unknown"
                direction = "stable"
            else:
                relative_change = round(
                    delta / abs(before_value),
                    4,
                )

                if abs(relative_change) < relative_threshold:
                    significance = "small"
                    direction = "stable"
                else:
                    significance = "relevant"

                    signed_change = (
                        relative_change
                        * direction_rule
                    )

                    if signed_change > 0:
                        direction = "positive"
                    elif signed_change < 0:
                        direction = "negative"
                    else:
                        direction = "stable"

            evaluations.append(
                TrainingMetricEvaluation(
                    metric_id=metric_id,
                    before=before_value,
                    after=after_value,
                    delta=delta,
                    relative_change=relative_change,
                    direction=direction,
                    significance=significance,
                )
            )

        total = len(metric_ids)
        resolved = len(evaluations)

        positive = sum(
            item.direction == "positive"
            for item in evaluations
        )
        stable = sum(
            item.direction == "stable"
            for item in evaluations
        )
        negative = sum(
            item.direction == "negative"
            for item in evaluations
        )

        result, reason = cls._classify(
            total=total,
            resolved=resolved,
            positive=positive,
            stable=stable,
            negative=negative,
            before_coverage=before_coverage,
            after_coverage=after_coverage,
            after_sample_size=after_sample_size,
        )

        confidence_score = cls._confidence_score(
            total=total,
            resolved=resolved,
            before_coverage=before_coverage,
            after_coverage=after_coverage,
            before_sample_size=before_sample_size,
            after_sample_size=after_sample_size,
            positive=positive,
            stable=stable,
            negative=negative,
        )

        confidence = cls._confidence_label(
            confidence_score
        )

        return TrainingCycleEvaluation(
            result=result,
            confidence=confidence,
            confidence_score=confidence_score,
            metrics_total=total,
            metrics_resolved=resolved,
            positive_metrics=positive,
            stable_metrics=stable,
            negative_metrics=negative,
            before_coverage=round(before_coverage, 2),
            after_coverage=round(after_coverage, 2),
            before_sample_size=before_sample_size,
            after_sample_size=after_sample_size,
            metric_evaluations=tuple(evaluations),
            reason=reason,
            caveat=(
                "O resultado descreve apenas a mudança observada entre "
                "as janelas. Não prova que o exercício causou a mudança."
            ),
        )

    @staticmethod
    def _classify(
        *,
        total: int,
        resolved: int,
        positive: int,
        stable: int,
        negative: int,
        before_coverage: float,
        after_coverage: float,
        after_sample_size: int,
    ) -> tuple[str, str]:
        if total == 0:
            return (
                "INCONCLUSIVE",
                "A missão não possui métricas avaliáveis.",
            )

        if resolved / total < 0.67:
            return (
                "INCONCLUSIVE",
                "Poucas métricas relacionadas à missão puderam ser avaliadas.",
            )

        if before_coverage < 80.0 or after_coverage < 80.0:
            return (
                "INCONCLUSIVE",
                "A cobertura de uma das janelas é insuficiente.",
            )

        if after_sample_size < 3:
            return (
                "INCONCLUSIVE",
                "A janela AFTER possui poucas partidas para avaliação.",
            )

        required_majority = (resolved // 2) + 1

        if positive >= required_majority and negative == 0:
            return (
                "POSITIVE",
                f"{positive} de {resolved} métricas avaliadas "
                "apresentaram mudança positiva relevante, sem sinal "
                "negativo contraditório.",
            )

        if negative >= required_majority and positive == 0:
            return (
                "NEGATIVE",
                f"{negative} de {resolved} métricas avaliadas "
                "apresentaram mudança negativa relevante, sem sinal "
                "positivo contraditório.",
            )

        if stable == resolved:
            return (
                "STABLE",
                "As métricas avaliadas permaneceram dentro da faixa "
                "considerada pequena para esta versão.",
            )

        return (
            "INCONCLUSIVE",
            "As métricas apresentaram sinais mistos ou insuficientemente "
            "consistentes para uma conclusão.",
        )

    @classmethod
    def _confidence_score(
        cls,
        *,
        total: int,
        resolved: int,
        before_coverage: float,
        after_coverage: float,
        before_sample_size: int,
        after_sample_size: int,
        positive: int,
        stable: int,
        negative: int,
    ) -> float:
        if total <= 0 or resolved <= 0:
            return 0.0

        metric_coverage = resolved / total

        data_coverage = (
            min(before_coverage, 100.0)
            + min(after_coverage, 100.0)
        ) / 200.0

        # A confiança cresce gradualmente conforme a janela AFTER aumenta.
        sample_factor = min(
            after_sample_size / 10.0,
            1.0,
        )

        before_factor = min(
            before_sample_size / 20.0,
            1.0,
        )

        dominant = max(
            positive,
            stable,
            negative,
        )
        agreement = dominant / resolved

        raw_score = (
            metric_coverage * 0.25
            + data_coverage * 0.20
            + sample_factor * 0.30
            + before_factor * 0.10
            + agreement * 0.15
        ) * 100.0

        # Proteção central da V1.1:
        # concordância perfeita não pode transformar 5 partidas em HIGH.
        if after_sample_size <= 5:
            ceiling = 69.99
        elif after_sample_size < 10:
            ceiling = 79.99
        else:
            ceiling = 100.0

        return round(
            min(
                raw_score,
                ceiling,
            ),
            2,
        )

    @staticmethod
    def _confidence_label(
        score: float,
    ) -> str:
        if score >= 80.0:
            return "HIGH"

        if score >= 60.0:
            return "MODERATE"

        return "LOW"
