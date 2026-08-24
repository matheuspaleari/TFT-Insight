"""
Resultado completo da análise de um jogador.
"""

from dataclasses import dataclass, field
from typing import Any

from .performance import Performance


@dataclass(slots=True, frozen=True)
class PlayerAnalysisResult:
    """
    Representa o resultado completo da análise de um jogador.

    Além da Performance, transporta os identificadores e o contexto
    competitivo necessários para persistência, Learning Engine,
    Inspector, Coach e interfaces.
    """

    puuid: str

    game_name: str
    tag_line: str

    current_rank: str
    current_stage: str
    target_stage: str
    profile_id: str

    benchmark_id: str

    match_ids: tuple[str, ...] = field(
        default_factory=tuple
    )

    performance: Performance | None = None

    competitive_spectrum: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.puuid.strip():
            raise ValueError(
                "PlayerAnalysisResult.puuid não pode ser vazio."
            )

        if not self.game_name.strip():
            raise ValueError(
                "PlayerAnalysisResult.game_name não pode ser vazio."
            )

        if not self.tag_line.strip():
            raise ValueError(
                "PlayerAnalysisResult.tag_line não pode ser vazia."
            )

        if not self.current_rank.strip():
            raise ValueError(
                "PlayerAnalysisResult.current_rank não pode ser vazio."
            )

        if not self.current_stage.strip():
            raise ValueError(
                "PlayerAnalysisResult.current_stage não pode ser vazio."
            )

        if not self.target_stage.strip():
            raise ValueError(
                "PlayerAnalysisResult.target_stage não pode ser vazio."
            )

        if not self.profile_id.strip():
            raise ValueError(
                "PlayerAnalysisResult.profile_id não pode ser vazio."
            )

        if not self.benchmark_id.strip():
            raise ValueError(
                "PlayerAnalysisResult.benchmark_id não pode ser vazio."
            )

        if not self.match_ids:
            raise ValueError(
                "PlayerAnalysisResult.match_ids deve possuir "
                "ao menos uma partida."
            )

        if self.performance is None:
            raise ValueError(
                "PlayerAnalysisResult.performance deve ser informado."
            )

    @property
    def riot_id(self) -> str:
        """
        Retorna o Riot ID completo.
        """

        return f"{self.game_name}#{self.tag_line}"