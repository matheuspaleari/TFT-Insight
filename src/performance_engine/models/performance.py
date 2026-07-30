from dataclasses import dataclass, field

from .priority import Priority


@dataclass(slots=True)
class Performance:
    """
    Representa o resultado final produzido pelo Performance Engine.

    Responsabilidade:
        Transportar a avaliação consolidada de performance do jogador.

    Entrada:
        Resultado calculado pelo PerformanceEngine.

    Saída:
        Dados consumidos pelos Services, Home, Dashboard e Coach AI.

    Este módulo:
        - Não calcula score.
        - Não define prioridades.
        - Não conhece a interface.
    """

    score: float
    status: str
    potential_score: float | None = None

    priorities: list[Priority] = field(default_factory=list)

    matches_analyzed: int = 0
    benchmark_name: str = ""

    def __post_init__(self) -> None:
        self.score = self._normalize_score(self.score)

        if self.potential_score is not None:
            self.potential_score = self._normalize_score(
                self.potential_score
            )

        if self.matches_analyzed < 0:
            raise ValueError(
                "Performance.matches_analyzed não pode ser negativo."
            )

        if not self.status.strip():
            raise ValueError("Performance.status não pode ser vazio.")

        self.priorities = sorted(
            self.priorities,
            key=lambda priority: priority.rank,
        )

    @staticmethod
    def _normalize_score(value: float) -> float:
        return round(max(0.0, min(100.0, float(value))), 2)

    @property
    def main_priority(self) -> Priority | None:
        """
        Retorna a prioridade de maior importância.

        Não calcula uma prioridade nova.
        Apenas acessa a primeira prioridade já ordenada.
        """
        return self.priorities[0] if self.priorities else None