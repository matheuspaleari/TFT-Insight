from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CompositionIntelligenceProfile:
    composition_key: str
    carry_character_id: str
    tank_character_id: str
    support_character_id: str
    primary_trait_names: tuple[str, ...] = field(default_factory=tuple)
    core_unit_ids: tuple[str, ...] = field(default_factory=tuple)

    matches_played: int = 0
    usage_rate: float = 0.0
    average_placement: float = 0.0
    top4_rate: float = 0.0
    win_rate: float = 0.0
    average_contest_score: float | None = None

    confidence_score: float = 0.0
    confidence_level: str = "Exploratória"
    recommendation_score: float = 0.0
    recommendation_label: str = "Exploratória"

    sample_is_reliable: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "composition_key": self.composition_key,
            "carry_character_id": self.carry_character_id,
            "tank_character_id": self.tank_character_id,
            "support_character_id": self.support_character_id,
            "primary_trait_names": list(self.primary_trait_names),
            "core_unit_ids": list(self.core_unit_ids),
            "matches_played": self.matches_played,
            "usage_rate": self.usage_rate,
            "average_placement": self.average_placement,
            "top4_rate": self.top4_rate,
            "win_rate": self.win_rate,
            "average_contest_score": self.average_contest_score,
            "confidence_score": self.confidence_score,
            "confidence_level": self.confidence_level,
            "recommendation_score": self.recommendation_score,
            "recommendation_label": self.recommendation_label,
            "sample_is_reliable": self.sample_is_reliable,
        }


@dataclass(frozen=True)
class CompositionIntelligenceReport:
    matches_analyzed: int
    unique_compositions: int
    diversity_rate: float
    repetition_rate: float

    repetition_signal: str
    repetition_interpretation: str

    most_used: CompositionIntelligenceProfile
    best_supported: CompositionIntelligenceProfile | None
    profiles: tuple[CompositionIntelligenceProfile, ...] = field(default_factory=tuple)

    limitations: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "matches_analyzed": self.matches_analyzed,
            "unique_compositions": self.unique_compositions,
            "diversity_rate": self.diversity_rate,
            "repetition_rate": self.repetition_rate,
            "repetition_signal": self.repetition_signal,
            "repetition_interpretation": self.repetition_interpretation,
            "most_used": self.most_used.to_dict(),
            "best_supported": (
                self.best_supported.to_dict()
                if self.best_supported
                else None
            ),
            "profiles": [item.to_dict() for item in self.profiles],
            "limitations": list(self.limitations),
        }
