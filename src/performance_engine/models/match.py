from dataclasses import dataclass, field

from .participant_snapshot import ParticipantSnapshot


@dataclass(slots=True, frozen=True)
class Match:
    """
    Representa uma partida completa e o jogador analisado.

    Os campos tradicionais foram mantidos para preservar compatibilidade
    com os calculadores atuais do Performance Engine.
    """

    match_id: str
    placement: int
    level: int
    gold_left: int
    last_round: int
    players_eliminated: int
    total_damage_to_players: int
    time_eliminated: float

    analyzed_player_puuid: str = ""
    participants: tuple[ParticipantSnapshot, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not self.match_id.strip():
            raise ValueError("match_id não pode ser vazio.")

        if not 1 <= self.placement <= 8:
            raise ValueError("placement deve estar entre 1 e 8.")

        if self.level < 1:
            raise ValueError("level deve ser maior ou igual a 1.")

        self._validate_non_negative("gold_left", self.gold_left)
        self._validate_non_negative("last_round", self.last_round)
        self._validate_non_negative(
            "players_eliminated",
            self.players_eliminated,
        )
        self._validate_non_negative(
            "total_damage_to_players",
            self.total_damage_to_players,
        )
        self._validate_non_negative(
            "time_eliminated",
            self.time_eliminated,
        )

        if (
            self.participants
            and not self.analyzed_player_puuid.strip()
        ):
            raise ValueError(
                "analyzed_player_puuid deve ser informado "
                "quando participants estiver preenchido."
            )

        participant_puuids = [
            participant.puuid
            for participant in self.participants
        ]

        if len(participant_puuids) != len(set(participant_puuids)):
            raise ValueError(
                "Match.participants não pode conter PUUIDs duplicados."
            )

        if (
            self.participants
            and self.analyzed_player_puuid not in participant_puuids
        ):
            raise ValueError(
                "O jogador analisado não foi encontrado em participants."
            )

    @property
    def analyzed_participant(self) -> ParticipantSnapshot | None:
        for participant in self.participants:
            if participant.puuid == self.analyzed_player_puuid:
                return participant

        return None

    @property
    def opponents(self) -> tuple[ParticipantSnapshot, ...]:
        return tuple(
            participant
            for participant in self.participants
            if participant.puuid != self.analyzed_player_puuid
        )

    @staticmethod
    def _validate_non_negative(
        name: str,
        value: int | float,
    ) -> None:
        if value < 0:
            raise ValueError(f"{name} não pode ser negativo.")
