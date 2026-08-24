from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class ContestFrequencyItem:
    item_id: str
    matches_observed: int
    match_rate: float
    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "matches_observed": self.matches_observed,
            "match_rate": self.match_rate,
        }

@dataclass(frozen=True)
class ContestBandDistribution:
    very_low: int = 0
    low: int = 0
    medium: int = 0
    high: int = 0
    extreme: int = 0
    def to_dict(self) -> dict[str, int]:
        return {
            "very_low": self.very_low,
            "low": self.low,
            "medium": self.medium,
            "high": self.high,
            "extreme": self.extreme,
        }

@dataclass(frozen=True)
class ContestPlacementComparison:
    high_contest_matches: int
    lower_contest_matches: int
    high_contest_average_placement: float | None
    lower_contest_average_placement: float | None
    placement_delta: float | None
    eligible_for_comparison: bool
    def to_dict(self) -> dict[str, Any]:
        return {
            "high_contest_matches": self.high_contest_matches,
            "lower_contest_matches": self.lower_contest_matches,
            "high_contest_average_placement": self.high_contest_average_placement,
            "lower_contest_average_placement": self.lower_contest_average_placement,
            "placement_delta": self.placement_delta,
            "eligible_for_comparison": self.eligible_for_comparison,
        }

@dataclass(frozen=True)
class LatestContestSnapshot:
    match_id: str
    score: float
    level: str
    carry_character_id: str
    carry_contested: bool
    opponents_contesting_carry: int
    opponents_with_shared_units: int
    opponents_with_shared_traits: int
    contested_unit_ids: tuple[str, ...] = field(default_factory=tuple)
    contested_trait_names: tuple[str, ...] = field(default_factory=tuple)
    def to_dict(self) -> dict[str, Any]:
        return {
            "match_id": self.match_id,
            "score": self.score,
            "level": self.level,
            "carry_character_id": self.carry_character_id,
            "carry_contested": self.carry_contested,
            "opponents_contesting_carry": self.opponents_contesting_carry,
            "opponents_with_shared_units": self.opponents_with_shared_units,
            "opponents_with_shared_traits": self.opponents_with_shared_traits,
            "contested_unit_ids": list(self.contested_unit_ids),
            "contested_trait_names": list(self.contested_trait_names),
        }

@dataclass(frozen=True)
class ContestIntelligenceReport:
    matches_analyzed: int
    average_score: float
    highest_score: float
    level: str
    high_contest_rate: float
    carry_contest_rate: float
    average_opponents_contesting_carry: float
    average_opponents_with_shared_units: float
    average_opponents_with_shared_traits: float
    band_distribution: ContestBandDistribution
    placement_comparison: ContestPlacementComparison
    most_contested_units: tuple[ContestFrequencyItem, ...]
    most_contested_traits: tuple[ContestFrequencyItem, ...]
    latest: LatestContestSnapshot
    limitations: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "matches_analyzed": self.matches_analyzed,
            "average_score": self.average_score,
            "highest_score": self.highest_score,
            "level": self.level,
            "high_contest_rate": self.high_contest_rate,
            "carry_contest_rate": self.carry_contest_rate,
            "average_opponents_contesting_carry": self.average_opponents_contesting_carry,
            "average_opponents_with_shared_units": self.average_opponents_with_shared_units,
            "average_opponents_with_shared_traits": self.average_opponents_with_shared_traits,
            "band_distribution": self.band_distribution.to_dict(),
            "placement_comparison": self.placement_comparison.to_dict(),
            "most_contested_units": [x.to_dict() for x in self.most_contested_units],
            "most_contested_traits": [x.to_dict() for x in self.most_contested_traits],
            "latest": self.latest.to_dict(),
            "limitations": list(self.limitations),
        }
