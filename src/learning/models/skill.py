from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class Skill:
    """
    Representa uma competência ensinável do TFT.

    Skills são conceitos apresentados ao usuário.
    Métricas permanecem como detalhes internos do sistema.
    """

    id: str
    title: str
    description: str

    prerequisite_ids: tuple[str, ...] = field(
        default_factory=tuple
    )

    related_metric_ids: tuple[str, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError(
                "Skill.id não pode ser vazio."
            )

        if not self.title.strip():
            raise ValueError(
                "Skill.title não pode ser vazio."
            )

        if not self.description.strip():
            raise ValueError(
                "Skill.description não pode ser vazia."
            )