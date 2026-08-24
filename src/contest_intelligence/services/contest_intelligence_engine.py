from __future__ import annotations
from collections import Counter
from statistics import mean

from src.decision_engine.models import ContestHistoryReport, ContestLevel
from src.contest_intelligence.models.contest_intelligence import (
    ContestBandDistribution,
    ContestFrequencyItem,
    ContestIntelligenceReport,
    ContestPlacementComparison,
    LatestContestSnapshot,
)

class ContestIntelligenceEngine:
    MIN_GROUP_SAMPLE = 3
    HIGH_CONTEST_THRESHOLD = 60.0

    @classmethod
    def build(cls, history: ContestHistoryReport) -> ContestIntelligenceReport:
        reports = history.match_reports
        if not reports:
            raise ValueError("ContestHistoryReport não contém partidas.")

        unit_counter = Counter(
            unit_id
            for report in reports
            for unit_id in set(report.contested_unit_ids)
        )
        trait_counter = Counter(
            trait_name
            for report in reports
            for trait_name in set(report.contested_trait_names)
        )

        high_count = sum(
            report.score > cls.HIGH_CONTEST_THRESHOLD
            for report in reports
        )
        lower_count = len(reports) - high_count

        placement = ContestPlacementComparison(
            high_contest_matches=high_count,
            lower_contest_matches=lower_count,
            high_contest_average_placement=history.contested_average_placement,
            lower_contest_average_placement=history.uncontested_average_placement,
            placement_delta=history.placement_impact,
            eligible_for_comparison=(
                high_count >= cls.MIN_GROUP_SAMPLE
                and lower_count >= cls.MIN_GROUP_SAMPLE
            ),
        )

        latest = history.latest_report

        return ContestIntelligenceReport(
            matches_analyzed=history.matches_analyzed,
            average_score=history.average_score,
            highest_score=history.highest_score,
            level=history.level.value,
            high_contest_rate=history.high_contest_rate,
            carry_contest_rate=history.carry_contest_rate,
            average_opponents_contesting_carry=round(
                mean(r.opponents_contesting_carry for r in reports), 2
            ),
            average_opponents_with_shared_units=round(
                mean(r.opponents_with_shared_units for r in reports), 2
            ),
            average_opponents_with_shared_traits=round(
                mean(r.opponents_with_shared_traits for r in reports), 2
            ),
            band_distribution=cls._bands(reports),
            placement_comparison=placement,
            most_contested_units=cls._frequency_items(unit_counter, history.matches_analyzed),
            most_contested_traits=cls._frequency_items(trait_counter, history.matches_analyzed),
            latest=LatestContestSnapshot(
                match_id=latest.match_id,
                score=latest.score,
                level=latest.level.value,
                carry_character_id=latest.carry_character_id,
                carry_contested=latest.carry_contested,
                opponents_contesting_carry=latest.opponents_contesting_carry,
                opponents_with_shared_units=latest.opponents_with_shared_units,
                opponents_with_shared_traits=latest.opponents_with_shared_traits,
                contested_unit_ids=latest.contested_unit_ids,
                contested_trait_names=latest.contested_trait_names,
            ),
            limitations=(
                "A contestação representa os boards finais observados; não reconstrói a disputa durante toda a partida.",
                "O sistema não sabe se o jogador fez scout nem como reagiu ao que estava disputado.",
                "Diferença de colocação entre grupos descreve associação histórica e não prova causalidade.",
                "Carry contestado não significa, sozinho, que manter a composição foi uma decisão incorreta.",
            ),
        )

    @staticmethod
    def _frequency_items(counter: Counter, matches: int):
        return tuple(
            ContestFrequencyItem(
                item_id=item_id,
                matches_observed=count,
                match_rate=round(count / matches * 100.0, 2),
            )
            for item_id, count in counter.most_common(5)
        )

    @staticmethod
    def _bands(reports):
        counter = Counter(report.level for report in reports)
        return ContestBandDistribution(
            very_low=counter[ContestLevel.VERY_LOW],
            low=counter[ContestLevel.LOW],
            medium=counter[ContestLevel.MEDIUM],
            high=counter[ContestLevel.HIGH],
            extreme=counter[ContestLevel.EXTREME],
        )
