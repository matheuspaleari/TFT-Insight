from dataclasses import dataclass, field

from .augment_snapshot import AugmentSnapshot
from .trait_snapshot import TraitSnapshot
from .unit_snapshot import UnitSnapshot


@dataclass(slots=True, frozen=True)
class ParticipantSnapshot:
    """
    Reúne os dados finais observáveis de um participante.

    Não reconstrói ações realizadas rodada a rodada.
    """

    puuid: str
    placement: int
    level: int
    gold_left: int
    last_round: int
    players_eliminated: int
    total_damage_to_players: int
    time_eliminated: float

    riot_id_game_name: str = ""
    riot_id_tag_line: str = ""

    traits: tuple[TraitSnapshot, ...] = field(default_factory=tuple)
    units: tuple[UnitSnapshot, ...] = field(default_factory=tuple)
    augments: tuple[AugmentSnapshot, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.puuid.strip():
            raise ValueError(
                "ParticipantSnapshot.puuid não pode ser vazio."
            )

        if not 1 <= self.placement <= 8:
            raise ValueError(
                "ParticipantSnapshot.placement deve estar entre 1 e 8."
            )

        if self.level < 1:
            raise ValueError(
                "ParticipantSnapshot.level deve ser maior ou igual a 1."
            )

        for field_name, value in (
            ("gold_left", self.gold_left),
            ("last_round", self.last_round),
            ("players_eliminated", self.players_eliminated),
            ("total_damage_to_players", self.total_damage_to_players),
            ("time_eliminated", self.time_eliminated),
        ):
            if value < 0:
                raise ValueError(
                    f"ParticipantSnapshot.{field_name} não pode ser negativo."
                )

    @property
    def riot_id(self) -> str:
        if (
            self.riot_id_game_name.strip()
            and self.riot_id_tag_line.strip()
        ):
            return (
                f"{self.riot_id_game_name}"
                f"#{self.riot_id_tag_line}"
            )

        return ""

    @property
    def active_traits(self) -> tuple[TraitSnapshot, ...]:
        return tuple(
            trait
            for trait in self.traits
            if trait.is_active
        )

    @property
    def unit_ids(self) -> frozenset[str]:
        return frozenset(
            unit.character_id
            for unit in self.units
        )

    @property
    def active_trait_names(self) -> frozenset[str]:
        return frozenset(
            trait.name
            for trait in self.active_traits
        )
