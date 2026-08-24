from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CompositionSimilarityV2Result:
    score: float

    carry_score: float
    tank_score: float
    trait_score: float
    unit_score: float

    structural_bonus: float = 0.0
    compatibility_cap_applied: bool = False
    compatibility_reason: str = ""

    shared_trait_names: tuple[str, ...] = field(default_factory=tuple)
    shared_unit_ids: tuple[str, ...] = field(default_factory=tuple)

    same_carry: bool = False
    same_tank: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "carry_score": self.carry_score,
            "tank_score": self.tank_score,
            "trait_score": self.trait_score,
            "unit_score": self.unit_score,
            "structural_bonus": self.structural_bonus,
            "compatibility_cap_applied": self.compatibility_cap_applied,
            "compatibility_reason": self.compatibility_reason,
            "shared_trait_names": list(self.shared_trait_names),
            "shared_unit_ids": list(self.shared_unit_ids),
            "same_carry": self.same_carry,
            "same_tank": self.same_tank,
        }


@dataclass(frozen=True)
class ClusterABSummary:
    engine: str
    cluster_count: int
    singleton_count: int
    largest_cluster_size: int
    average_cluster_size: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine": self.engine,
            "cluster_count": self.cluster_count,
            "singleton_count": self.singleton_count,
            "largest_cluster_size": self.largest_cluster_size,
            "average_cluster_size": self.average_cluster_size,
        }


@dataclass(frozen=True)
class PairDecisionChange:
    first_match_id: str
    second_match_id: str

    first_carry: str
    second_carry: str

    v1_score: float
    v2_score: float

    v1_merge: bool
    v2_merge: bool

    change_type: str

    shared_traits: tuple[str, ...] = field(default_factory=tuple)
    shared_units: tuple[str, ...] = field(default_factory=tuple)

    v2_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "first_match_id": self.first_match_id,
            "second_match_id": self.second_match_id,
            "first_carry": self.first_carry,
            "second_carry": self.second_carry,
            "v1_score": self.v1_score,
            "v2_score": self.v2_score,
            "v1_merge": self.v1_merge,
            "v2_merge": self.v2_merge,
            "change_type": self.change_type,
            "shared_traits": list(self.shared_traits),
            "shared_units": list(self.shared_units),
            "v2_reason": self.v2_reason,
        }


@dataclass(frozen=True)
class CompositionSimilarityABReport:
    snapshot_count: int
    threshold: float

    v1: ClusterABSummary
    v2: ClusterABSummary

    old_merge_new_split: tuple[PairDecisionChange, ...]
    old_split_new_merge: tuple[PairDecisionChange, ...]

    same_carry_pairs: int
    same_carry_merged_v1: int
    same_carry_merged_v2: int

    support_used_by_v2: bool = False

    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_count": self.snapshot_count,
            "threshold": self.threshold,
            "v1": self.v1.to_dict(),
            "v2": self.v2.to_dict(),
            "old_merge_new_split": [
                item.to_dict()
                for item in self.old_merge_new_split
            ],
            "old_split_new_merge": [
                item.to_dict()
                for item in self.old_split_new_merge
            ],
            "same_carry_pairs": self.same_carry_pairs,
            "same_carry_merged_v1": self.same_carry_merged_v1,
            "same_carry_merged_v2": self.same_carry_merged_v2,
            "support_used_by_v2": self.support_used_by_v2,
            "notes": list(self.notes),
        }
