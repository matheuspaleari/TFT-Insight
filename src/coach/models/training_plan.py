from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class TrainingPlan:
    """
    Representa um plano estruturado de evolução para o jogador.

    O plano é produzido pelo próprio TFT Insight com base
    nas prioridades calculadas pelo Performance Engine.

    A IA não define o plano. Ela apenas poderá transformar
    essas informações em uma comunicação mais natural.
    """

    focus_metric_id: str
    focus_title: str

    objective: str
    diagnosis: str

    games_target: int = 5

    actions: tuple[str, ...] = field(
        default_factory=tuple
    )

    checklist: tuple[str, ...] = field(
        default_factory=tuple
    )

    common_mistakes: tuple[str, ...] = field(
        default_factory=tuple
    )

    expected_improvements: tuple[str, ...] = field(
        default_factory=tuple
    )

    monitored_metrics: tuple[str, ...] = field(
        default_factory=tuple
    )

    learning_title: str = ""
    learning_content: str = ""

    def __post_init__(self) -> None:
        if not self.focus_metric_id.strip():
            raise ValueError(
                "TrainingPlan.focus_metric_id não pode ser vazio."
            )

        if not self.focus_title.strip():
            raise ValueError(
                "TrainingPlan.focus_title não pode ser vazio."
            )

        if not self.objective.strip():
            raise ValueError(
                "TrainingPlan.objective não pode ser vazio."
            )

        if not self.diagnosis.strip():
            raise ValueError(
                "TrainingPlan.diagnosis não pode ser vazio."
            )

        if self.games_target < 1:
            raise ValueError(
                "TrainingPlan.games_target deve ser maior que zero."
            )

        if not self.actions:
            raise ValueError(
                "TrainingPlan.actions deve possuir ao menos uma ação."
            )

        if not self.checklist:
            raise ValueError(
                "TrainingPlan.checklist deve possuir ao menos um item."
            )

        if not self.monitored_metrics:
            raise ValueError(
                "TrainingPlan.monitored_metrics deve possuir "
                "ao menos uma métrica."
            )