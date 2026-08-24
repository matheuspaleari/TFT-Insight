"""
Relatório histórico das composições utilizadas.
"""

from dataclasses import dataclass, field

from .composition_profile import CompositionProfile
from .composition_snapshot import CompositionSnapshot


@dataclass(slots=True, frozen=True)
class CompositionHistoryReport:
    """
    Resume repetição, diversidade e desempenho das composições.
    """

    matches_analyzed: int

    unique_compositions: int
    diversity_rate: float
    repetition_rate: float

    most_used_composition: CompositionProfile
    best_composition: CompositionProfile
    worst_composition: CompositionProfile

    latest_composition: CompositionSnapshot

    profiles: tuple[CompositionProfile, ...] = field(
        default_factory=tuple
    )
    snapshots: tuple[CompositionSnapshot, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if self.matches_analyzed < 1:
            raise ValueError(
                "matches_analyzed deve ser maior que zero."
            )

        if self.matches_analyzed != len(self.snapshots):
            raise ValueError(
                "matches_analyzed deve corresponder aos snapshots."
            )

        if self.unique_compositions < 1:
            raise ValueError(
                "unique_compositions deve ser maior que zero."
            )

        for field_name, value in (
            ("diversity_rate", self.diversity_rate),
            ("repetition_rate", self.repetition_rate),
        ):
            if not 0.0 <= value <= 100.0:
                raise ValueError(
                    f"{field_name} deve estar entre 0 e 100."
                )

    @property
    def forces_composition(self) -> bool:
        """
        Sinaliza repetição elevada da composição mais usada.

        Esta é uma heurística inicial, não uma prova de intenção.
        """

        return self.repetition_rate >= 50.0
