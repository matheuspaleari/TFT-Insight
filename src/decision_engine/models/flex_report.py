from dataclasses import dataclass, field

from .composition_snapshot import CompositionSnapshot
from .flex_level import FlexLevel


@dataclass(slots=True, frozen=True)
class FlexReport:
    matches_analyzed: int
    score: float
    level: FlexLevel

    unique_compositions: int
    unique_carries: int
    unique_tanks: int

    composition_diversity_rate: float
    carry_diversity_rate: float
    tank_diversity_rate: float
    repetition_rate: float

    latest_composition: CompositionSnapshot

    snapshots: tuple[CompositionSnapshot, ...] = field(
        default_factory=tuple
    )

    @property
    def likely_forces_composition(self) -> bool:
        return self.repetition_rate >= 50.0
