"""
Resultado da comparação entre duas composições.
"""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CompositionSimilarity:
    """
    Detalha a similaridade entre duas assinaturas de composição.
    """

    score: float

    carry_score: float
    trait_score: float
    unit_score: float

    shared_trait_names: tuple[str, ...] = ()
    shared_unit_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name, value in (
            ("score", self.score),
            ("carry_score", self.carry_score),
            ("trait_score", self.trait_score),
            ("unit_score", self.unit_score),
        ):
            if not 0.0 <= value <= 100.0:
                raise ValueError(
                    f"{field_name} deve estar entre 0 e 100."
                )
