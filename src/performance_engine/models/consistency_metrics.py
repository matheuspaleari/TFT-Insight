from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ConsistencyMetrics:
    """
    Métricas que representam a variação dos resultados do jogador.
    """

    placement_variance: float
    placement_standard_deviation: float
    bottom4_rate: float
    best_placement: int
    worst_placement: int

    def __post_init__(self) -> None:
        if self.placement_variance < 0:
            raise ValueError("placement_variance não pode ser negativa.")

        if self.placement_standard_deviation < 0:
            raise ValueError(
                "placement_standard_deviation não pode ser negativo."
            )

        if not 0.0 <= self.bottom4_rate <= 100.0:
            raise ValueError("bottom4_rate deve estar entre 0 e 100.")

        if not 1 <= self.best_placement <= 8:
            raise ValueError("best_placement deve estar entre 1 e 8.")

        if not 1 <= self.worst_placement <= 8:
            raise ValueError("worst_placement deve estar entre 1 e 8.")

        if self.best_placement > self.worst_placement:
            raise ValueError(
                "best_placement não pode ser maior que worst_placement."
            )