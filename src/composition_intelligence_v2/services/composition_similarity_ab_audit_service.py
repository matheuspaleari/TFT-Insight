from __future__ import annotations

from src.decision_engine.analyzers.composition_cluster_analyzer import (
    CompositionClusterAnalyzer,
)
from src.decision_engine.analyzers.composition_similarity_analyzer import (
    CompositionSimilarityAnalyzer,
)
from src.decision_engine.models import CompositionSnapshot

from src.composition_intelligence_v2.models.composition_similarity_v2 import (
    ClusterABSummary,
    CompositionSimilarityABReport,
    PairDecisionChange,
)
from src.composition_intelligence_v2.services.composition_cluster_analyzer_v2 import (
    CompositionClusterAnalyzerV2,
)
from src.composition_intelligence_v2.services.composition_similarity_analyzer_v2 import (
    CompositionSimilarityAnalyzerV2,
)


class CompositionSimilarityABAuditService:
    @classmethod
    def analyze(
        cls,
        snapshots: tuple[CompositionSnapshot, ...],
        *,
        threshold: float = 55.0,
    ) -> CompositionSimilarityABReport:
        if len(
            snapshots
        ) < 2:
            raise ValueError(
                "A/B Audit precisa de pelo menos 2 snapshots."
            )

        v1_clusters = (
            CompositionClusterAnalyzer.cluster(
                snapshots,
                threshold=threshold,
            )
        )

        v2_clusters = (
            CompositionClusterAnalyzerV2.cluster(
                snapshots,
                threshold=threshold,
            )
        )

        old_merge_new_split = []
        old_split_new_merge = []

        same_carry_pairs = 0
        same_carry_merged_v1 = 0
        same_carry_merged_v2 = 0

        for first_index, first in enumerate(
            snapshots
        ):
            for second in snapshots[
                first_index + 1:
            ]:
                v1 = (
                    CompositionSimilarityAnalyzer.compare(
                        first,
                        second,
                    )
                )
                v2 = (
                    CompositionSimilarityAnalyzerV2.compare(
                        first,
                        second,
                    )
                )

                v1_merge = (
                    v1.score
                    >= threshold
                )
                v2_merge = (
                    v2.score
                    >= threshold
                )

                if (
                    first.carry_character_id
                    and first.carry_character_id
                    == second.carry_character_id
                ):
                    same_carry_pairs += 1
                    same_carry_merged_v1 += int(
                        v1_merge
                    )
                    same_carry_merged_v2 += int(
                        v2_merge
                    )

                if (
                    v1_merge
                    == v2_merge
                ):
                    continue

                change_type = (
                    "OLD_MERGE_NEW_SPLIT"
                    if (
                        v1_merge
                        and not v2_merge
                    )
                    else "OLD_SPLIT_NEW_MERGE"
                )

                item = PairDecisionChange(
                    first_match_id=(
                        first.match_id
                    ),
                    second_match_id=(
                        second.match_id
                    ),
                    first_carry=(
                        first.carry_character_id
                    ),
                    second_carry=(
                        second.carry_character_id
                    ),
                    v1_score=v1.score,
                    v2_score=v2.score,
                    v1_merge=v1_merge,
                    v2_merge=v2_merge,
                    change_type=change_type,
                    shared_traits=(
                        v2.shared_trait_names
                    ),
                    shared_units=(
                        v2.shared_unit_ids
                    ),
                    v2_reason=(
                        v2.compatibility_reason
                    ),
                )

                if (
                    change_type
                    == "OLD_MERGE_NEW_SPLIT"
                ):
                    old_merge_new_split.append(
                        item
                    )
                else:
                    old_split_new_merge.append(
                        item
                    )

        return CompositionSimilarityABReport(
            snapshot_count=len(
                snapshots
            ),
            threshold=threshold,
            v1=cls._summary(
                "V1",
                v1_clusters,
            ),
            v2=cls._summary(
                "V2",
                v2_clusters,
            ),
            old_merge_new_split=tuple(
                sorted(
                    old_merge_new_split,
                    key=lambda item: (
                        item.v1_score
                        - item.v2_score
                    ),
                    reverse=True,
                )
            ),
            old_split_new_merge=tuple(
                sorted(
                    old_split_new_merge,
                    key=lambda item: (
                        item.v2_score
                        - item.v1_score
                    ),
                    reverse=True,
                )
            ),
            same_carry_pairs=(
                same_carry_pairs
            ),
            same_carry_merged_v1=(
                same_carry_merged_v1
            ),
            same_carry_merged_v2=(
                same_carry_merged_v2
            ),
            support_used_by_v2=False,
            notes=(
                "V2 não usa Support no score porque a auditoria real "
                "encontrou 0/30 Supports identificados.",
                "V2 aumenta o peso do carry e adiciona tank como sinal "
                "secundário de identidade.",
                "Trait igual sozinho não deve superar baixo overlap de "
                "board quando o carry é diferente.",
                "Carry diferente ainda pode ser variante do mesmo "
                "arquétipo se traits e core units forem fortemente "
                "sobrepostos.",
                "Este relatório é A/B; ele ainda não substitui a V1 "
                "no pipeline principal.",
            ),
        )

    @staticmethod
    def _summary(
        engine: str,
        clusters,
    ) -> ClusterABSummary:
        sizes = [
            len(
                cluster.snapshots
            )
            for cluster in clusters
        ]

        return ClusterABSummary(
            engine=engine,
            cluster_count=len(
                clusters
            ),
            singleton_count=sum(
                size == 1
                for size in sizes
            ),
            largest_cluster_size=max(
                sizes
            ),
            average_cluster_size=round(
                sum(
                    sizes
                )
                / len(
                    sizes
                ),
                2,
            ),
        )
