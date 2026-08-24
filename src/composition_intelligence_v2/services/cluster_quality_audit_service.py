from __future__ import annotations

from statistics import median

from src.decision_engine.analyzers.composition_cluster_analyzer import (
    CompositionClusterAnalyzer,
)
from src.decision_engine.analyzers.composition_similarity_analyzer import (
    CompositionSimilarityAnalyzer,
)
from src.decision_engine.constants.composition_similarity import (
    COMPOSITION_CLUSTER_THRESHOLD,
)
from src.decision_engine.models import CompositionSnapshot

from src.composition_intelligence_v2.models.cluster_quality_audit import (
    ClusterQualityAuditReport,
    PairSimilarityAudit,
    ThresholdSimulation,
)


class ClusterQualityAuditService:
    DEFAULT_THRESHOLDS = (
        45.0,
        50.0,
        55.0,
        60.0,
        65.0,
    )

    BOUNDARY_WINDOW = 7.5

    @classmethod
    def analyze(
        cls,
        snapshots: tuple[CompositionSnapshot, ...],
        *,
        current_threshold: float = COMPOSITION_CLUSTER_THRESHOLD,
        thresholds: tuple[float, ...] = DEFAULT_THRESHOLDS,
    ) -> ClusterQualityAuditReport:
        if len(snapshots) < 2:
            raise ValueError(
                "Cluster Quality Audit precisa de pelo menos 2 snapshots."
            )

        pairs = cls._pairwise(
            snapshots=snapshots,
            current_threshold=current_threshold,
        )

        scores = sorted(
            item.total_score
            for item in pairs
        )

        near_boundary = tuple(
            sorted(
                (
                    item
                    for item in pairs
                    if item.near_boundary
                ),
                key=lambda item: (
                    abs(item.distance_to_current_threshold),
                    -item.total_score,
                ),
            )
        )

        # "Separado" aqui significa somente score abaixo do threshold.
        # Não assumimos que o algoritmo final colocou ou não o par
        # no mesmo cluster por transitividade/representante.
        highest_separated = tuple(
            sorted(
                (
                    item
                    for item in pairs
                    if item.total_score < current_threshold
                ),
                key=lambda item: item.total_score,
                reverse=True,
            )[:10]
        )

        lowest_merged = tuple(
            sorted(
                (
                    item
                    for item in pairs
                    if item.total_score >= current_threshold
                ),
                key=lambda item: item.total_score,
            )[:10]
        )

        simulations = tuple(
            cls._simulate_threshold(
                snapshots=snapshots,
                threshold=threshold,
            )
            for threshold in thresholds
        )

        support_identified = sum(
            bool(snapshot.support_character_id)
            for snapshot in snapshots
        )

        support_missing = (
            len(snapshots)
            - support_identified
        )

        return ClusterQualityAuditReport(
            snapshot_count=len(snapshots),
            current_threshold=current_threshold,
            pair_count=len(pairs),
            minimum_similarity=round(scores[0], 2),
            median_similarity=round(median(scores), 2),
            maximum_similarity=round(scores[-1], 2),
            near_boundary_pairs=near_boundary,
            highest_separated_pairs=highest_separated,
            lowest_merged_pairs=lowest_merged,
            threshold_simulations=simulations,
            support_identified_count=support_identified,
            support_missing_count=support_missing,
            support_identification_rate=round(
                support_identified
                / len(snapshots)
                * 100.0,
                2,
            ),
            notes=(
                "Este audit mede sensibilidade do clustering; ele não escolhe "
                "automaticamente um novo threshold.",
                "Quantidade menor de clusters não significa qualidade melhor: "
                "um threshold baixo pode juntar arquétipos realmente diferentes.",
                "Carry pesa 25%, traits 50% e core units 25% no score atual.",
                "Support ausente não é preenchido artificialmente; a auditoria "
                "mede se a inferência atual realmente encontra esse papel.",
            ),
        )

    @classmethod
    def _pairwise(
        cls,
        *,
        snapshots: tuple[CompositionSnapshot, ...],
        current_threshold: float,
    ) -> tuple[PairSimilarityAudit, ...]:
        result: list[PairSimilarityAudit] = []

        for first_index, first in enumerate(
            snapshots
        ):
            for second in snapshots[
                first_index + 1:
            ]:
                similarity = (
                    CompositionSimilarityAnalyzer.compare(
                        first,
                        second,
                    )
                )

                distance = round(
                    similarity.score
                    - current_threshold,
                    2,
                )

                result.append(
                    PairSimilarityAudit(
                        first_match_id=first.match_id,
                        second_match_id=second.match_id,
                        total_score=similarity.score,
                        carry_score=similarity.carry_score,
                        trait_score=similarity.trait_score,
                        unit_score=similarity.unit_score,
                        first_carry=first.carry_character_id,
                        second_carry=second.carry_character_id,
                        shared_traits=similarity.shared_trait_names,
                        shared_units=similarity.shared_unit_ids,
                        distance_to_current_threshold=distance,
                        near_boundary=(
                            abs(distance)
                            <= cls.BOUNDARY_WINDOW
                        ),
                    )
                )

        return tuple(result)

    @staticmethod
    def _simulate_threshold(
        *,
        snapshots: tuple[CompositionSnapshot, ...],
        threshold: float,
    ) -> ThresholdSimulation:
        clusters = (
            CompositionClusterAnalyzer.cluster(
                snapshots,
                threshold=threshold,
            )
        )

        sizes = [
            len(cluster.snapshots)
            for cluster in clusters
        ]

        return ThresholdSimulation(
            threshold=threshold,
            cluster_count=len(clusters),
            singleton_count=sum(
                size == 1
                for size in sizes
            ),
            largest_cluster_size=max(sizes),
            average_cluster_size=round(
                sum(sizes)
                / len(sizes),
                2,
            ),
        )
