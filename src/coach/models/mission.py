"""
Modelo que representa a missão prática atribuída ao jogador.
"""

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class Mission:
    """
    Representa o foco de treinamento para as próximas partidas.

    A missão possui um objetivo único e uma quantidade definida
    de partidas para que o jogador pratique esse objetivo.
    """

    title: str
    description: str

    focus_metric_id: str

    games_target: int = 5
    games_completed: int = 0

    checklist: tuple[str, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError(
                "Mission.title não pode ser vazio."
            )

        if not self.description.strip():
            raise ValueError(
                "Mission.description não pode ser vazia."
            )

        if not self.focus_metric_id.strip():
            raise ValueError(
                "Mission.focus_metric_id não pode ser vazio."
            )

        if self.games_target < 1:
            raise ValueError(
                "Mission.games_target deve ser maior que zero."
            )

        if self.games_completed < 0:
            raise ValueError(
                "Mission.games_completed não pode ser negativo."
            )

        if self.games_completed > self.games_target:
            raise ValueError(
                "Mission.games_completed não pode ser maior "
                "que Mission.games_target."
            )

        if not self.checklist:
            raise ValueError(
                "Mission.checklist deve possuir ao menos um item."
            )

    @property
    def is_completed(self) -> bool:
        """
        Informa se a missão já foi concluída.
        """

        return self.games_completed >= self.games_target

    @property
    def remaining_games(self) -> int:
        """
        Retorna quantas partidas ainda faltam.
        """

        return max(
            0,
            self.games_target - self.games_completed,
        )

    @property
    def progress_percentage(self) -> float:
        """
        Retorna o progresso percentual da missão.
        """

        progress = (
            self.games_completed
            / self.games_target
        ) * 100.0

        return round(progress, 1)

    @property
    def progress_bar(self) -> str:
        """
        Produz uma representação simples do progresso.

        Exemplo:
            ■■□□□
        """

        completed = "■" * self.games_completed
        remaining = "□" * self.remaining_games

        return completed + remaining