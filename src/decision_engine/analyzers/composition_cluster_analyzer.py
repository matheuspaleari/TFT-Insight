"""
Agrupamento de composições semelhantes.
"""

from src.decision_engine.constants.composition_similarity import (
    COMPOSITION_CLUSTER_THRESHOLD,
)
from src.decision_engine.models import (
    CompositionCluster,
    CompositionSnapshot,
)

from .composition_similarity_analyzer import (
    CompositionSimilarityAnalyzer,
)


class CompositionClusterAnalyzer:
    """
    Agrupa variantes da mesma composição usando similaridade híbrida.

    O algoritmo é determinístico e preserva a ordem das partidas:
    a primeira composição de cada grupo vira seu representante inicial.
    """

    @classmethod
    def cluster(
        cls,
        snapshots: tuple[CompositionSnapshot, ...],
        *,
        threshold: float = COMPOSITION_CLUSTER_THRESHOLD,
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
            best_cluster_index: int | None = None
            best_score = -1.0

            for index, group in enumerate(
                mutable_clusters
            ):
                representative = group[0]

                similarity = (
                    CompositionSimilarityAnalyzer.compare(
                        snapshot,
                        representative,
                    )
                )

                if (
                    similarity.score >= threshold
                    and similarity.score > best_score
                ):
                    best_cluster_index = index
                    best_score = similarity.score

            if best_cluster_index is None:
                mutable_clusters.append(
                    [snapshot]
                )
            else:
                mutable_clusters[
                    best_cluster_index
                ].append(snapshot)

        clusters = []

        for index, group in enumerate(
            mutable_clusters,
            start=1,
        ):
            representative = (
                cls._select_representative(
                    group
                )
            )

            ordered_group = tuple(
                sorted(
                    group,
                    key=lambda snapshot: (
                        snapshot.match_id
                        != representative.match_id
                    ),
                )
            )

            clusters.append(
                CompositionCluster(
                    cluster_id=(
                        f"composition_{index}"
                    ),
                    representative=representative,
                    snapshots=ordered_group,
                )
            )

        return tuple(clusters)

    @classmethod
    def _select_representative(
        cls,
        snapshots: list[CompositionSnapshot],
    ) -> CompositionSnapshot:
        """
        Seleciona a composição mais central do grupo.
        """

        if len(snapshots) == 1:
            return snapshots[0]

        best_snapshot = snapshots[0]
        best_average_similarity = -1.0

        for candidate in snapshots:
            similarities = [
                CompositionSimilarityAnalyzer.compare(
                    candidate,
                    other,
                ).score
                for other in snapshots
                if other is not candidate
            ]

            average_similarity = (
                sum(similarities)
                / len(similarities)
                if similarities
                else 100.0
            )

            if (
                average_similarity
                > best_average_similarity
            ):
                best_snapshot = candidate
                best_average_similarity = (
                    average_similarity
                )

        return best_snapshot
