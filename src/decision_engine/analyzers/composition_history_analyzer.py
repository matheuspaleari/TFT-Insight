from statistics import mean

from src.decision_engine.models import (
    CompositionHistoryReport,
    CompositionProfile,
    CompositionSnapshot,
    ContestHistoryReport,
)
from src.performance_engine.models import Match
from src.role_inference.models import ItemClassification

from .composition_analyzer import CompositionAnalyzer
from .composition_cluster_analyzer import (
    CompositionClusterAnalyzer,
)


class CompositionHistoryAnalyzer:
    @classmethod
    def analyze(
        cls,
        matches: list[Match],
        *,
        contest_history: ContestHistoryReport | None = None,
        item_classifications: dict[
            str,
            ItemClassification,
        ] | None = None,
    ) -> CompositionHistoryReport:
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

        contest_score_by_match_id = {}

        if contest_history is not None:
            contest_score_by_match_id = {
                report.match_id: report.score
                for report in contest_history.match_reports
            }

        clusters = CompositionClusterAnalyzer.cluster(
            snapshots
        )

        profiles = tuple(
            cls._build_profile(
                composition_key=cluster.cluster_id,
                representative=cluster.representative,
                snapshots=list(cluster.snapshots),
                total_matches=len(snapshots),
                contest_score_by_match_id=(
                    contest_score_by_match_id
                ),
            )
            for cluster in clusters
        )

        most_used = max(
            profiles,
            key=lambda profile: (
                profile.matches_played,
                -profile.average_placement,
            ),
        )
        best = min(
            profiles,
            key=lambda profile: (
                profile.average_placement,
                -profile.matches_played,
            ),
        )
        worst = max(
            profiles,
            key=lambda profile: (
                profile.average_placement,
                profile.matches_played,
            ),
        )

        unique_compositions = len(profiles)

        return CompositionHistoryReport(
            matches_analyzed=len(snapshots),
            unique_compositions=unique_compositions,
            diversity_rate=round(
                unique_compositions / len(snapshots) * 100.0,
                2,
            ),
            repetition_rate=round(
                most_used.matches_played
                / len(snapshots)
                * 100.0,
                2,
            ),
            most_used_composition=most_used,
            best_composition=best,
            worst_composition=worst,
            latest_composition=snapshots[0],
            profiles=tuple(
                sorted(
                    profiles,
                    key=lambda profile: (
                        profile.matches_played,
                        -profile.average_placement,
                    ),
                    reverse=True,
                )
            ),
            snapshots=snapshots,
        )

    @staticmethod
    def _build_profile(
        *,
        composition_key: str,
        representative: CompositionSnapshot,
        snapshots: list[CompositionSnapshot],
        total_matches: int,
        contest_score_by_match_id: dict[str, float],
    ) -> CompositionProfile:
        placements = [
            snapshot.placement
            for snapshot in snapshots
        ]

        contest_scores = [
            contest_score_by_match_id[snapshot.match_id]
            for snapshot in snapshots
            if snapshot.match_id in contest_score_by_match_id
        ]

        return CompositionProfile(
            composition_key=composition_key,
            carry_character_id=(
                representative.carry_character_id
            ),
            matches_played=len(snapshots),
            usage_rate=round(
                len(snapshots) / total_matches * 100.0,
                2,
            ),
            average_placement=round(
                mean(placements),
                2,
            ),
            top4_rate=round(
                sum(value <= 4 for value in placements)
                / len(placements)
                * 100.0,
                2,
            ),
            win_rate=round(
                sum(value == 1 for value in placements)
                / len(placements)
                * 100.0,
                2,
            ),
            average_contest_score=(
                round(mean(contest_scores), 2)
                if contest_scores
                else None
            ),
        )
