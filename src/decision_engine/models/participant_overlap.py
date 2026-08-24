"""
Sobreposição entre o jogador analisado e um adversário.
"""

from dataclasses import dataclass, field

from .contest_level import ContestLevel


@dataclass(slots=True, frozen=True)
class ParticipantOverlap:
    """
    Representa a contestação causada por um adversário específico.
    """

    opponent_puuid: str
    opponent_riot_id: str

    shared_unit_ids: tuple[str, ...] = field(
        default_factory=tuple
    )
    shared_trait_names: tuple[str, ...] = field(
        default_factory=tuple
    )

    unit_overlap_percentage: float = 0.0
    trait_overlap_percentage: float = 0.0

    carry_contested: bool = False
    carry_character_id: str = ""

    score: float = 0.0
    level: ContestLevel = ContestLevel.VERY_LOW

    def __post_init__(self) -> None:
        if not self.opponent_puuid.strip():
            raise ValueError(
                "ParticipantOverlap.opponent_puuid "
                "não pode ser vazio."
            )

        for field_name, value in (
            (
                "unit_overlap_percentage",
                self.unit_overlap_percentage,
            ),
            (
                "trait_overlap_percentage",
                self.trait_overlap_percentage,
            ),
            ("score", self.score),
        ):
            if not 0.0 <= value <= 100.0:
                raise ValueError(
                    f"{field_name} deve estar entre 0 e 100."
                )

        if (
            self.carry_contested
            and not self.carry_character_id.strip()
        ):
            raise ValueError(
                "carry_character_id deve ser informado "
                "quando carry_contested=True."
            )

    @property
    def shared_units_count(self) -> int:
        return len(self.shared_unit_ids)

    @property
    def shared_traits_count(self) -> int:
        return len(self.shared_trait_names)
