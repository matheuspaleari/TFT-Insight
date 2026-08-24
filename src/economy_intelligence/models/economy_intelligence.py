from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EconomyFinalStateDistribution:
    gold_0_to_5: int
    gold_6_to_19: int
    gold_20_plus: int
    level_7_or_lower: int
    level_8: int
    level_9_plus: int

    def to_dict(self) -> dict[str, int]:
        return {
            "gold_0_to_5": self.gold_0_to_5,
            "gold_6_to_19": self.gold_6_to_19,
            "gold_20_plus": self.gold_20_plus,
            "level_7_or_lower": self.level_7_or_lower,
            "level_8": self.level_8,
            "level_9_plus": self.level_9_plus,
        }


@dataclass(frozen=True)
class EconomyPlacementComparison:
    level_9_plus_matches: int
    below_level_9_matches: int
    level_9_plus_average_placement: float | None
    below_level_9_average_placement: float | None
    placement_delta: float | None
    eligible_for_comparison: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "level_9_plus_matches": self.level_9_plus_matches,
            "below_level_9_matches": self.below_level_9_matches,
            "level_9_plus_average_placement": self.level_9_plus_average_placement,
            "below_level_9_average_placement": self.below_level_9_average_placement,
            "placement_delta": self.placement_delta,
            "eligible_for_comparison": self.eligible_for_comparison,
        }


@dataclass(frozen=True)
class EconomyRecentTrend:
    recent_matches: int
    previous_matches: int
    recent_average_level: float | None
    previous_average_level: float | None
    level_delta: float | None
    recent_average_gold_left: float | None
    previous_average_gold_left: float | None
    gold_delta: float | None
    recent_average_placement: float | None
    previous_average_placement: float | None
    placement_delta: float | None
    signal: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "recent_matches": self.recent_matches,
            "previous_matches": self.previous_matches,
            "recent_average_level": self.recent_average_level,
            "previous_average_level": self.previous_average_level,
            "level_delta": self.level_delta,
            "recent_average_gold_left": self.recent_average_gold_left,
            "previous_average_gold_left": self.previous_average_gold_left,
            "gold_delta": self.gold_delta,
            "recent_average_placement": self.recent_average_placement,
            "previous_average_placement": self.previous_average_placement,
            "placement_delta": self.placement_delta,
            "signal": self.signal,
        }


@dataclass(frozen=True)
class LatestEconomySnapshot:
    match_id: str
    placement: int
    level: int
    gold_left: int
    last_round: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "match_id": self.match_id,
            "placement": self.placement,
            "level": self.level,
            "gold_left": self.gold_left,
            "last_round": self.last_round,
        }


@dataclass(frozen=True)
class EconomyIntelligenceReport:
    matches_analyzed: int
    score: float
    label: str

    average_level: float
    median_level: float
    average_gold_left: float
    median_gold_left: float
    average_last_round: float

    level_8_rate: float
    level_9_rate: float
    low_level_late_rate: float

    distribution: EconomyFinalStateDistribution
    placement_comparison: EconomyPlacementComparison
    recent_trend: EconomyRecentTrend
    latest: LatestEconomySnapshot

    limitations: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "matches_analyzed": self.matches_analyzed,
            "score": self.score,
            "label": self.label,
            "average_level": self.average_level,
            "median_level": self.median_level,
            "average_gold_left": self.average_gold_left,
            "median_gold_left": self.median_gold_left,
            "average_last_round": self.average_last_round,
            "level_8_rate": self.level_8_rate,
            "level_9_rate": self.level_9_rate,
            "low_level_late_rate": self.low_level_late_rate,
            "distribution": self.distribution.to_dict(),
            "placement_comparison": self.placement_comparison.to_dict(),
            "recent_trend": self.recent_trend.to_dict(),
            "latest": self.latest.to_dict(),
            "limitations": list(self.limitations),
        }
