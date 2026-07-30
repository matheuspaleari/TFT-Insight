from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Match:
    """
    Representa os dados observáveis de um jogador em uma partida.
    """

    match_id: str
    placement: int
    level: int
    gold_left: int
    last_round: int
    players_eliminated: int
    total_damage_to_players: int
    time_eliminated: float

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

    @staticmethod
    def _validate_non_negative(
        name: str,
        value: int | float,
    ) -> None:
        if value < 0:
            raise ValueError(f"{name} não pode ser negativo.")