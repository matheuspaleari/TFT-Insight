from __future__ import annotations

from typing import Any


class TrainingMetricResolver:
    """
    Resolve IDs públicos de métricas para a estrutura real de PlayerMetrics.

    Mantém o Training Engine desacoplado do layout interno das métricas.
    """

    _PATHS: dict[str, tuple[str, ...]] = {
        "average_level": (
            "general",
            "average_level",
        ),
        "average_damage_to_players": (
            "combat",
            "average_damage_to_players",
        ),
        "average_players_eliminated": (
            "combat",
            "average_players_eliminated",
        ),
        "placement_standard_deviation": (
            "consistency",
            "placement_standard_deviation",
        ),
        "average_gold_left": (
            "economy",
            "average_gold_left",
        ),
    }

    @classmethod
    def resolve(
        cls,
        *,
        player_metrics: Any,
        metric_id: str,
    ) -> float | int | None:
        path = cls._PATHS.get(metric_id)

        if path is None:
            return None

        value: Any = player_metrics

        for attribute in path:
            value = getattr(
                value,
                attribute,
                None,
            )

            if value is None:
                return None

        if isinstance(
            value,
            (int, float),
        ):
            return value

        return None

    @classmethod
    def resolve_many(
        cls,
        *,
        player_metrics: Any,
        metric_ids: tuple[str, ...],
    ) -> dict[str, float | int | None]:
        return {
            metric_id: cls.resolve(
                player_metrics=player_metrics,
                metric_id=metric_id,
            )
            for metric_id in metric_ids
        }

    @staticmethod
    def delta(
        *,
        before: float | int | None,
        after: float | int | None,
    ) -> float | None:
        if not isinstance(
            before,
            (int, float),
        ):
            return None

        if not isinstance(
            after,
            (int, float),
        ):
            return None

        return round(
            float(after) - float(before),
            4,
        )
