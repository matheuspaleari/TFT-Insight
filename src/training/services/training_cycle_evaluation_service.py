from __future__ import annotations

from typing import Any

from src.integration_engine.services.cached_match_service import (
    CachedMatchService,
)
from src.performance_engine.calculators import (
    PlayerMetricsCalculator,
)
from src.storage import PlayerRepository
from src.training.services.training_cycle_evaluation_engine import (
    TrainingCycleEvaluationEngine,
)
from src.training.services.training_cycle_window_service import (
    TrainingCycleWindowService,
)
from src.training.services.training_metric_resolver import (
    TrainingMetricResolver,
)


class TrainingCycleEvaluationService:
    """
    Orquestra reconstrução, cálculo e persistência de avaliações de ciclo.

    A classificação continua totalmente determinística.
    """

    def __init__(
        self,
        *,
        cached_match_service: CachedMatchService | None = None,
        metrics_calculator: PlayerMetricsCalculator | None = None,
        player_repository: PlayerRepository | None = None,
    ) -> None:
        self.cached_match_service = (
            cached_match_service
            or CachedMatchService()
        )
        self.metrics_calculator = (
            metrics_calculator
            or PlayerMetricsCalculator()
        )
        self.player_repository = (
            player_repository
            or PlayerRepository()
        )

    def evaluate_cycle_if_needed(
        self,
        *,
        puuid: str,
        cycle: dict[str, Any],
    ) -> dict[str, Any]:
        existing = cycle.get(
            "evaluation"
        )

        if isinstance(
            existing,
            dict,
        ):
            return cycle

        windows = (
            TrainingCycleWindowService.reconstruct(
                puuid=puuid,
                cycle=cycle,
                cached_match_service=(
                    self.cached_match_service
                ),
            )
        )

        before_metrics = (
            self.metrics_calculator.calculate(
                matches=(
                    windows
                    .before
                    .load_result
                    .matches
                )
            )
        )

        after_metrics = (
            self.metrics_calculator.calculate(
                matches=(
                    windows
                    .after
                    .load_result
                    .matches
                )
            )
        )

        before_values = (
            TrainingMetricResolver.resolve_many(
                player_metrics=before_metrics,
                metric_ids=(
                    windows.related_metric_ids
                ),
            )
        )

        after_values = (
            TrainingMetricResolver.resolve_many(
                player_metrics=after_metrics,
                metric_ids=(
                    windows.related_metric_ids
                ),
            )
        )

        evaluation = (
            TrainingCycleEvaluationEngine.evaluate(
                before_metrics=before_values,
                after_metrics=after_values,
                before_coverage=(
                    windows.before.coverage
                ),
                after_coverage=(
                    windows.after.coverage
                ),
                before_sample_size=(
                    windows.before.loaded_count
                ),
                after_sample_size=(
                    windows.after.loaded_count
                ),
            )
        )

        payload = evaluation.to_dict()

        self.player_repository.save_training_cycle_evaluation(
            puuid=puuid,
            cycle_id=windows.cycle_id,
            evaluation=payload,
        )

        updated = dict(
            cycle
        )
        updated["evaluation"] = payload

        return updated

    def evaluate_pending_cycles(
        self,
        *,
        puuid: str,
        cycles: list[dict[str, Any]],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Avalia ciclos sem resultado. Falha de um ciclo não bloqueia os demais.

        O limite evita trabalho excessivo em contas com histórico longo.
        """

        evaluated: list[
            dict[str, Any]
        ] = []

        for index, cycle in enumerate(
            cycles
        ):
            if index >= limit:
                evaluated.extend(
                    cycles[index:]
                )
                break

            try:
                evaluated.append(
                    self.evaluate_cycle_if_needed(
                        puuid=puuid,
                        cycle=cycle,
                    )
                )
            except (
                RuntimeError,
                ValueError,
                KeyError,
            ):
                evaluated.append(
                    cycle
                )

        return evaluated
