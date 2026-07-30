from dataclasses import dataclass, field

from .performance import Performance


@dataclass(slots=True)
class HomeData:
    """
    Representa os dados prontos para exibição na Home.

    Responsabilidade:
        Transportar os dados que serão apresentados ao jogador.

    Entrada:
        Performance e resumo da sessão preparados pelo HomeService.

    Saída:
        Objeto consumido pela interface.

    Este módulo:
        - Não calcula performance.
        - Não acessa a Riot API.
        - Não possui código de Streamlit.
    """

    player_name: str
    performance: Performance

    session_summary: str = ""
    coach_message: str = ""

    lp_change: int = 0
    matches_played: int = 0

    highlights: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.player_name.strip():
            raise ValueError("HomeData.player_name não pode ser vazio.")

        if self.matches_played < 0:
            raise ValueError(
                "HomeData.matches_played não pode ser negativo."
            )