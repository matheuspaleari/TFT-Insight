from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ItemFrequency:
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
class BuildProfile:
    item_ids: tuple[str, ...]
    matches_played: int
    average_placement: float
    top4_rate: float
    win_rate: float
    eligible_for_comparison: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_ids": list(self.item_ids),
            "matches_played": self.matches_played,
            "average_placement": self.average_placement,
            "top4_rate": self.top4_rate,
            "win_rate": self.win_rate,
            "eligible_for_comparison": self.eligible_for_comparison,
        }


@dataclass(frozen=True)
class CarryProfile:
    character_id: str
    matches_played: int
    usage_rate: float
    average_placement: float
    top4_rate: float
    win_rate: float
    full_build_rate: float
    eligible_for_comparison: bool
    most_used_items: tuple[ItemFrequency, ...]
    recurring_builds: tuple[BuildProfile, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "character_id": self.character_id,
            "matches_played": self.matches_played,
            "usage_rate": self.usage_rate,
            "average_placement": self.average_placement,
            "top4_rate": self.top4_rate,
            "win_rate": self.win_rate,
            "full_build_rate": self.full_build_rate,
            "eligible_for_comparison": self.eligible_for_comparison,
            "most_used_items": [
                item.to_dict()
                for item in self.most_used_items
            ],
            "recurring_builds": [
                build.to_dict()
                for build in self.recurring_builds
            ],
        }


@dataclass(frozen=True)
class LatestCarrySnapshot:
    match_id: str
    placement: int
    character_id: str
    item_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "match_id": self.match_id,
            "placement": self.placement,
            "character_id": self.character_id,
            "item_ids": list(self.item_ids),
        }


@dataclass(frozen=True)
class CarryItemIntelligenceReport:
    matches_analyzed: int
    matches_with_carry: int
    carry_detection_rate: float

    itemization_score: float
    itemization_label: str
    carry_item_share: float
    carry_full_item_rate: float

    unique_carries: int
    carry_profiles: tuple[CarryProfile, ...]
    most_used_carry: CarryProfile | None
    best_supported_carry: CarryProfile | None

    latest: LatestCarrySnapshot | None
    limitations: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "matches_analyzed": self.matches_analyzed,
            "matches_with_carry": self.matches_with_carry,
            "carry_detection_rate": self.carry_detection_rate,
            "itemization_score": self.itemization_score,
            "itemization_label": self.itemization_label,
            "carry_item_share": self.carry_item_share,
            "carry_full_item_rate": self.carry_full_item_rate,
            "unique_carries": self.unique_carries,
            "carry_profiles": [
                profile.to_dict()
                for profile in self.carry_profiles
            ],
            "most_used_carry": (
                self.most_used_carry.to_dict()
                if self.most_used_carry
                else None
            ),
            "best_supported_carry": (
                self.best_supported_carry.to_dict()
                if self.best_supported_carry
                else None
            ),
            "latest": (
                self.latest.to_dict()
                if self.latest
                else None
            ),
            "limitations": list(self.limitations),
        }
