from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class CoachMetric:
    """
    Representa uma métrica preparada para consumo pelo Coach.

    Reúne dados da avaliação, da prioridade e dos metadados
    em um único objeto.
    """

    id: str
    title: str
    category: str

    player_value: float
    benchmark_value: float

    score: float
    weight: float
    impact: float

    description: str

    drivers: tuple[str, ...] = field(
        default_factory=tuple
    )

    recommendations: tuple[str, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError(
                "CoachMetric.id não pode ser vazio."
            )

        if not self.title.strip():
            raise ValueError(
                "CoachMetric.title não pode ser vazio."
            )

        if not self.category.strip():
            raise ValueError(
                "CoachMetric.category não pode ser vazia."
            )

        if not 0.0 <= self.score <= 100.0:
            raise ValueError(
                "CoachMetric.score deve estar entre 0 e 100."
            )

        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(
                "CoachMetric.weight deve estar entre 0 e 1."
            )

        if self.impact < 0:
            raise ValueError(
                "CoachMetric.impact não pode ser negativo."
            )