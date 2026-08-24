from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PairSimilarityAudit:
    first_match_id: str
    second_match_id: str

    total_score: float
    carry_score: float
    trait_score: float
    unit_score: float

    first_carry: str
    second_carry: str
    shared_traits: tuple[str, ...] = field(default_factory=tuple)
    shared_units: tuple[str, ...] = field(default_factory=tuple)

    distance_to_current_threshold: float = 0.0
    near_boundary: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "first_match_id": self.first_match_id,
            "second_match_id": self.second_match_id,
            "total_score": self.total_score,
            "carry_score": self.carry_score,
            "trait_score": self.trait_score,
            "unit_score": self.unit_score,
            "first_carry": self.first_carry,
            "second_carry": self.second_carry,
            "shared_traits": list(self.shared_traits),
            "shared_units": list(self.shared_units),
            "distance_to_current_threshold": self.distance_to_current_threshold,
            "near_boundary": self.near_boundary,
        }


@dataclass(frozen=True)
class ThresholdSimulation:
    threshold: float
    cluster_count: int
    singleton_count: int
    largest_cluster_size: int
    average_cluster_size: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "threshold": self.threshold,
            "cluster_count": self.cluster_count,
            "singleton_count": self.singleton_count,
            "largest_cluster_size": self.largest_cluster_size,
            "average_cluster_size": self.average_cluster_size,
        }


@dataclass(frozen=True)
class ClusterQualityAuditReport:
    snapshot_count: int
    current_threshold: float

    pair_count: int
    minimum_similarity: float
    median_similarity: float
    maximum_similarity: float

    near_boundary_pairs: tuple[PairSimilarityAudit, ...]
    highest_separated_pairs: tuple[PairSimilarityAudit, ...]
    lowest_merged_pairs: tuple[PairSimilarityAudit, ...]

    threshold_simulations: tuple[ThresholdSimulation, ...]

    support_identified_count: int
    support_missing_count: int
    support_identification_rate: float

    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_count": self.snapshot_count,
            "current_threshold": self.current_threshold,
            "pair_count": self.pair_count,
            "minimum_similarity": self.minimum_similarity,
            "median_similarity": self.median_similarity,
            "maximum_similarity": self.maximum_similarity,
            "near_boundary_pairs": [
                item.to_dict()
                for item in self.near_boundary_pairs
            ],
            "highest_separated_pairs": [
                item.to_dict()
                for item in self.highest_separated_pairs
            ],
            "lowest_merged_pairs": [
                item.to_dict()
                for item in self.lowest_merged_pairs
            ],
            "threshold_simulations": [
                item.to_dict()
                for item in self.threshold_simulations
            ],
            "support_identified_count": self.support_identified_count,
            "support_missing_count": self.support_missing_count,
            "support_identification_rate": self.support_identification_rate,
            "notes": list(self.notes),
        }
