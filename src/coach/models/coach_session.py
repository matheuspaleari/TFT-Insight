"""
Modelo principal de uma sessão de treinamento do TFT Insight.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from .mission import Mission
from .session_evolution import SessionEvolution
from .training_plan import TrainingPlan


@dataclass(slots=True, frozen=True)
class CoachSession:
    """
    Representa uma sessão completa de treinamento.

    Cada análise produz uma CoachSession contendo:

    - resumo da análise;
    - plano de treinamento;
    - missão prática;
    - progresso da missão;
    - comparação com uma sessão anterior, quando disponível.
    """

    summary: str

    score: float
    status: str

    benchmark_name: str
    matches_analyzed: int

    training_plan: TrainingPlan
    mission: Mission

    evolution: SessionEvolution | None = None

    session_id: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.summary.strip():
            raise ValueError(
                "CoachSession.summary não pode ser vazio."
            )

        if not 0.0 <= self.score <= 100.0:
            raise ValueError(
                "CoachSession.score deve estar entre 0 e 100."
            )

        if not self.status.strip():
            raise ValueError(
                "CoachSession.status não pode ser vazio."
            )

        if not self.benchmark_name.strip():
            raise ValueError(
                "CoachSession.benchmark_name não pode ser vazio."
            )

        if self.matches_analyzed < 1:
            raise ValueError(
                "CoachSession.matches_analyzed deve ser "
                "maior que zero."
            )

        if (
            self.training_plan.focus_metric_id
            != self.mission.focus_metric_id
        ):
            raise ValueError(
                "A missão e o plano de treinamento devem possuir "
                "a mesma métrica de foco."
            )

        if not self.session_id:
            object.__setattr__(
                self,
                "session_id",
                str(uuid4()),
            )

        if not self.created_at:
            created_at = datetime.now(
                timezone.utc
            ).isoformat()

            object.__setattr__(
                self,
                "created_at",
                created_at,
            )

    @property
    def focus_title(self) -> str:
        """
        Retorna o título do foco atual.
        """

        return self.training_plan.focus_title

    @property
    def mission_completed(self) -> bool:
        """
        Informa se a missão da sessão foi concluída.
        """

        return self.mission.is_completed