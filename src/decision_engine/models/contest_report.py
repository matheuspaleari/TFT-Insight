"""
Relatório consolidado de contestação de uma partida.
"""

from dataclasses import dataclass, field

from .contest_level import ContestLevel
from .participant_overlap import ParticipantOverlap


@dataclass(slots=True, frozen=True)
class ContestReport:
    """
    Resume a contestação final da composição do jogador.
    """

    match_id: str
    analyzed_player_puuid: str

    score: float
    level: ContestLevel

    carry_character_id: str = ""
    carry_contested: bool = False

    contested_unit_ids: tuple[str, ...] = field(
        default_factory=tuple
    )
    contested_trait_names: tuple[str, ...] = field(
        default_factory=tuple
    )

    opponents_with_shared_units: int = 0
    opponents_with_shared_traits: int = 0
    opponents_contesting_carry: int = 0

    overlaps: tuple[ParticipantOverlap, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not self.match_id.strip():
            raise ValueError(
                "ContestReport.match_id não pode ser vazio."
            )

        if not self.analyzed_player_puuid.strip():
            raise ValueError(
                "ContestReport.analyzed_player_puuid "
                "não pode ser vazio."
            )

        if not 0.0 <= self.score <= 100.0:
            raise ValueError(
                "ContestReport.score deve estar entre 0 e 100."
            )

        for field_name, value in (
            (
                "opponents_with_shared_units",
                self.opponents_with_shared_units,
            ),
            (
                "opponents_with_shared_traits",
                self.opponents_with_shared_traits,
            ),
            (
                "opponents_contesting_carry",
                self.opponents_contesting_carry,
            ),
        ):
            if value < 0:
                raise ValueError(
                    f"{field_name} não pode ser negativo."
                )

    @property
    def worst_opponent(
        self,
    ) -> ParticipantOverlap | None:
        """
        Retorna o adversário com maior score de contestação.
        """

        if not self.overlaps:
            return None

        return max(
            self.overlaps,
            key=lambda overlap: overlap.score,
        )
