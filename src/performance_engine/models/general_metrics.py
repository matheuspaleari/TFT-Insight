from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class GeneralMetrics:
    """
    Métricas gerais calculadas a partir do histórico de partidas.

    Todos os percentuais usam a escala de 0 a 100.
    """

    matches_played: int
    average_placement: float
    top4_rate: float
    win_rate: float
    average_level: float

    def __post_init__(self) -> None:
        if self.matches_played < 0:
            raise ValueError("matches_played não pode ser negativo.")

        if not 1.0 <= self.average_placement <= 8.0:
            raise ValueError(
                "average_placement deve estar entre 1 e 8."
            )

        if not 0.0 <= self.average_level <= 10.0:
            raise ValueError("average_level deve estar entre 0 e 10.")

        self._validate_percentage("top4_rate", self.top4_rate)
        self._validate_percentage("win_rate", self.win_rate)

    @staticmethod
    def _validate_percentage(name: str, value: float) -> None:
        if not 0.0 <= value <= 100.0:
            raise ValueError(f"{name} deve estar entre 0 e 100.")