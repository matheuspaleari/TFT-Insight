from dataclasses import dataclass, field

from .coach_metric import CoachMetric


@dataclass(slots=True, frozen=True)
class CoachContext:
    """
    Representa todo o contexto estruturado utilizado pelo Coach.

    Este modelo não gera texto e não consulta IA.
    Ele apenas transporta os resultados já calculados pelo
    Performance Engine.
    """

    score: float
    status: str

    benchmark_name: str
    matches_analyzed: int

    potential_score: float | None = None

    metrics: tuple[CoachMetric, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 100.0:
            raise ValueError(
                "CoachContext.score deve estar entre 0 e 100."
            )

        if self.potential_score is not None:
            if not 0.0 <= self.potential_score <= 100.0:
                raise ValueError(
                    "CoachContext.potential_score deve estar "
                    "entre 0 e 100."
                )

        if not self.status.strip():
            raise ValueError(
                "CoachContext.status não pode ser vazio."
            )

        if not self.benchmark_name.strip():
            raise ValueError(
                "CoachContext.benchmark_name não pode ser vazio."
            )

        if self.matches_analyzed < 1:
            raise ValueError(
                "CoachContext.matches_analyzed deve ser maior que zero."
            )

    @property
    def main_metric(self) -> CoachMetric | None:
        """
        Retorna a métrica de maior prioridade para o Coach.
        """

        return self.metrics[0] if self.metrics else None