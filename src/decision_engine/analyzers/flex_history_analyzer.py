from src.decision_engine.models import (
    FlexLevel,
    FlexReport,
)
from src.performance_engine.models import Match
from src.role_inference.models import ItemClassification

from .composition_analyzer import CompositionAnalyzer
from .composition_cluster_analyzer import (
    CompositionClusterAnalyzer,
)


class FlexHistoryAnalyzer:
    """
    Mede flexibilidade nas últimas partidas.

    Score:
    - 45% diversidade de composições;
    - 30% diversidade de carries;
    - 15% diversidade de tanks;
    - 10% ausência de repetição excessiva.
    """

    @classmethod
    def analyze(
        cls,
        matches: list[Match],
        *,
        item_classifications: dict[
            str,
            ItemClassification,
        ],
    ) -> FlexReport:
        if not matches:
            raise ValueError(
                "É necessário informar ao menos uma partida."
            )

        snapshots = tuple(
            CompositionAnalyzer.analyze(
                match,
                item_classifications=item_classifications,
            )
            for match in matches
        )

        clusters = CompositionClusterAnalyzer.cluster(
            snapshots
        )

        total = len(snapshots)
        unique_compositions = len(clusters)

        carries = {
            snapshot.carry_character_id
            for snapshot in snapshots
            if snapshot.carry_character_id
        }

        tanks = {
            snapshot.tank_character_id
            for snapshot in snapshots
            if snapshot.tank_character_id
        }

        largest_cluster = max(
            cluster.matches_played
            for cluster in clusters
        )

        composition_diversity = (
            unique_compositions / total * 100.0
        )
        carry_diversity = (
            len(carries) / total * 100.0
        )
        tank_diversity = (
            len(tanks) / total * 100.0
        )
        repetition_rate = (
            largest_cluster / total * 100.0
        )

        score = (
            composition_diversity * 0.45
            + carry_diversity * 0.30
            + tank_diversity * 0.15
            + (100.0 - repetition_rate) * 0.10
        )

        return FlexReport(
            matches_analyzed=total,
            score=round(score, 2),
            level=FlexLevel.from_score(score),
            unique_compositions=unique_compositions,
            unique_carries=len(carries),
            unique_tanks=len(tanks),
            composition_diversity_rate=round(
                composition_diversity,
                2,
            ),
            carry_diversity_rate=round(
                carry_diversity,
                2,
            ),
            tank_diversity_rate=round(
                tank_diversity,
                2,
            ),
            repetition_rate=round(
                repetition_rate,
                2,
            ),
            latest_composition=snapshots[0],
            snapshots=snapshots,
        )
