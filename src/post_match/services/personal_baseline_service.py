from __future__ import annotations

import math
import statistics
from typing import Any

from src.post_match.models import (
    PersonalBaselineReport,
    PersonalComparisonBand,
    PersonalMetricComparison,
)


class PersonalBaselineService:
    MIN_BASELINE_MATCHES = 5
    DEFAULT_HISTORY_SIZE = 10
    Z_THRESHOLD = 0.75

    METRICS = (
        ("placement", "Colocação", False),
        ("level", "Nível final", True),
        ("gold_left", "Ouro restante", True),
        (
            "total_damage_to_players",
            "Dano aos jogadores",
            True,
        ),
        (
            "players_eliminated",
            "Jogadores eliminados",
            True,
        ),
    )

    @classmethod
    def compare(
        cls,
        *,
        target_match: Any,
        prior_matches: list[Any],
        requested_history_size: int = DEFAULT_HISTORY_SIZE,
    ) -> PersonalBaselineReport:
        history = [
            match
            for match in prior_matches
            if str(match.match_id)
            != str(target_match.match_id)
        ][:requested_history_size]

        comparisons = tuple(
            cls._compare_metric(
                target_match=target_match,
                history=history,
                metric_id=metric_id,
                label=label,
                higher_is_better=higher_is_better,
            )
            for (
                metric_id,
                label,
                higher_is_better,
            )
            in cls.METRICS
        )

        if len(history) < cls.MIN_BASELINE_MATCHES:
            summary = (
                f"Há apenas {len(history)} partida(s) anteriores. "
                f"O baseline pessoal exige pelo menos "
                f"{cls.MIN_BASELINE_MATCHES}; por isso nenhuma diferença "
                "é tratada como tendência pessoal."
            )
        else:
            above = sum(
                item.band == PersonalComparisonBand.ABOVE
                for item in comparisons
            )
            within = sum(
                item.band == PersonalComparisonBand.WITHIN
                for item in comparisons
            )
            below = sum(
                item.band == PersonalComparisonBand.BELOW
                for item in comparisons
            )
            summary = (
                f"Comparação com {len(history)} partidas anteriores: "
                f"{above} acima do padrão pessoal, {within} dentro do "
                f"padrão e {below} abaixo. Isso contextualiza a partida, "
                "mas não prova execução da missão."
            )

        return PersonalBaselineReport(
            target_match_id=str(target_match.match_id),
            requested_history_size=requested_history_size,
            matches_used=len(history),
            comparisons=comparisons,
            summary=summary,
            changes_evidence_class=False,
            changes_learning_priority=False,
            counts_as_mission_evidence=False,
        )

    @classmethod
    def _compare_metric(
        cls,
        *,
        target_match: Any,
        history: list[Any],
        metric_id: str,
        label: str,
        higher_is_better: bool,
    ) -> PersonalMetricComparison:
        current = float(
            getattr(
                target_match,
                metric_id,
            )
        )

        values = [
            float(
                getattr(
                    match,
                    metric_id,
                )
            )
            for match in history
        ]

        if len(values) < cls.MIN_BASELINE_MATCHES:
            return PersonalMetricComparison(
                metric_id=metric_id,
                label=label,
                current_value=current,
                baseline_mean=(
                    statistics.mean(values)
                    if values
                    else None
                ),
                baseline_std=None,
                sample_size=len(values),
                higher_is_better=higher_is_better,
                band=PersonalComparisonBand.INSUFFICIENT,
            )

        mean = statistics.mean(values)
        std = statistics.pstdev(values)
        delta = current - mean

        if math.isclose(
            std,
            0.0,
            abs_tol=1e-9,
        ):
            raw_z = 0.0 if math.isclose(
                delta,
                0.0,
                abs_tol=1e-9,
            ) else (
                math.inf
                if delta > 0
                else -math.inf
            )
        else:
            raw_z = delta / std

        oriented_z = (
            raw_z
            if higher_is_better
            else -raw_z
        )

        if oriented_z >= cls.Z_THRESHOLD:
            band = PersonalComparisonBand.ABOVE
        elif oriented_z <= -cls.Z_THRESHOLD:
            band = PersonalComparisonBand.BELOW
        else:
            band = PersonalComparisonBand.WITHIN

        return PersonalMetricComparison(
            metric_id=metric_id,
            label=label,
            current_value=current,
            baseline_mean=mean,
            baseline_std=std,
            sample_size=len(values),
            higher_is_better=higher_is_better,
            band=band,
            delta=delta,
            z_score=(
                oriented_z
                if math.isfinite(oriented_z)
                else oriented_z
            ),
        )
