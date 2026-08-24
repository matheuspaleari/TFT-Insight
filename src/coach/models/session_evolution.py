"""
Modelo utilizado para representar a evolução entre sessões do Coach.
"""

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class SessionEvolution:
    """
    Representa a comparação entre duas sessões de treinamento.

    Este modelo não realiza o cálculo da evolução.
    Ele apenas transporta o resultado da comparação.
    """

    previous_score: float
    current_score: float
    score_change: float

    previous_focus_metric_id: str
    current_focus_metric_id: str

    focus_changed: bool
    previous_focus_improved: bool

    summary: str

    improved_metrics: tuple[str, ...] = field(
        default_factory=tuple
    )

    declined_metrics: tuple[str, ...] = field(
        default_factory=tuple
    )

    stable_metrics: tuple[str, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not 0.0 <= self.previous_score <= 100.0:
            raise ValueError(
                "SessionEvolution.previous_score deve estar "
                "entre 0 e 100."
            )

        if not 0.0 <= self.current_score <= 100.0:
            raise ValueError(
                "SessionEvolution.current_score deve estar "
                "entre 0 e 100."
            )

        if not self.previous_focus_metric_id.strip():
            raise ValueError(
                "SessionEvolution.previous_focus_metric_id "
                "não pode ser vazio."
            )

        if not self.current_focus_metric_id.strip():
            raise ValueError(
                "SessionEvolution.current_focus_metric_id "
                "não pode ser vazio."
            )

        if not self.summary.strip():
            raise ValueError(
                "SessionEvolution.summary não pode ser vazio."
            )