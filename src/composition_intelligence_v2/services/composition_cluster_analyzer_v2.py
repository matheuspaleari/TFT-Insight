from __future__ import annotations

from src.decision_engine.models import (
    CompositionCluster,
    CompositionSnapshot,
)

from src.composition_intelligence_v2.services.composition_similarity_analyzer_v2 import (
    CompositionSimilarityAnalyzerV2,
)


class CompositionClusterAnalyzerV2:
    """
    Clustering determinístico usando CompositionSimilarityAnalyzerV2.

    Mantém o comportamento geral da V1 para permitir comparação A/B
    justa: ordem das partidas e representante inicial.
    """

    @classmethod
    def cluster(
        cls,
        snapshots: tuple[CompositionSnapshot, ...],
        *,
        threshold: float = 55.0,
    ) -> tuple[CompositionCluster, ...]:
        if not snapshots:
            raise ValueError(
                "É necessário informar ao menos uma composição."
            )

        if not 0.0 <= threshold <= 100.0:
            raise ValueError(
                "O threshold deve estar entre 0 e 100."
            )

        mutable_clusters: list[
            list[CompositionSnapshot]
        ] = []

        for snapshot in snapshots:
            best_cluster_index = None
            best_score = -1.0

            for index, group in enumerate(
                mutable_clusters
            ):
                representative = group[0]

                similarity = (
                    CompositionSimilarityAnalyzerV2.compare(
                        snapshot,
                        representative,
                    )
                )

                if (
                    similarity.score
                    >= threshold
                    and similarity.score
                    > best_score
                ):
                    best_cluster_index = (
                        index
                    )
                    best_score = (
                        similarity.score
                    )

            if best_cluster_index is None:
                mutable_clusters.append(
                    [snapshot]
                )
            else:
                mutable_clusters[
                    best_cluster_index
                ].append(
                    snapshot
                )

        result = []

        for index, group in enumerate(
            mutable_clusters,
            start=1,
        ):
            representative = (
                cls._select_representative(
                    group
                )
            )

            ordered = tuple(
                sorted(
                    group,
                    key=lambda item: (
                        item.match_id
                        != representative.match_id
                    ),
                )
            )

            result.append(
                CompositionCluster(
                    cluster_id=(
                        f"composition_v2_{index}"
                    ),
                    representative=(
                        representative
                    ),
                    snapshots=ordered,
                )
            )

        return tuple(
            result
        )

    @classmethod
    def _select_representative(
        cls,
        snapshots: list[CompositionSnapshot],
    ) -> CompositionSnapshot:
        if len(
            snapshots
        ) == 1:
            return snapshots[0]

        best = snapshots[0]
        best_average = -1.0

        for candidate in snapshots:
            scores = [
                CompositionSimilarityAnalyzerV2.compare(
                    candidate,
                    other,
                ).score
                for other in snapshots
                if other is not candidate
            ]

            average = (
                sum(
                    scores
                )
                / len(
                    scores
                )
                if scores
                else 100.0
            )

            if average > best_average:
                best = candidate
                best_average = average

        return best
