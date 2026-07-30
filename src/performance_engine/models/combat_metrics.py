from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CombatMetrics:
    """
    Métricas relacionadas ao resultado dos combates.

    Os campos devem ser preenchidos somente quando os dados estiverem
    disponíveis e tiverem uma definição comprovada.
    """

    average_damage_to_players: float | None = None
    average_players_eliminated: float | None = None

    def __post_init__(self) -> None:
        self._validate_optional_non_negative(
            "average_damage_to_players",
            self.average_damage_to_players,
        )
        self._validate_optional_non_negative(
            "average_players_eliminated",
            self.average_players_eliminated,
        )

    @staticmethod
    def _validate_optional_non_negative(
        name: str,
        value: float | None,
    ) -> None:
        if value is not None and value < 0:
            raise ValueError(f"{name} não pode ser negativo.")