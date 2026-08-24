"""
Modelo que representa um estágio competitivo do TFT Insight.
"""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class BenchmarkGroup:
    """
    Agrupa elos da Riot que compartilham o mesmo estágio competitivo.

    O benchmark associado ao grupo representa o padrão que os jogadores
    desse estágio devem buscar para alcançar o estágio-alvo.
    """

    id: str
    benchmark_id: str
    display_name: str

    current_ranks: tuple[str, ...]

    target_stage: str

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError(
                "BenchmarkGroup.id não pode ser vazio."
            )

        if not self.benchmark_id.strip():
            raise ValueError(
                "BenchmarkGroup.benchmark_id não pode ser vazio."
            )

        if not self.display_name.strip():
            raise ValueError(
                "BenchmarkGroup.display_name não pode ser vazio."
            )

        if not self.current_ranks:
            raise ValueError(
                "BenchmarkGroup.current_ranks deve possuir "
                "ao menos um elo."
            )

        if not self.target_stage.strip():
            raise ValueError(
                "BenchmarkGroup.target_stage não pode ser vazio."
            )

    def contains_rank(
        self,
        rank: str,
    ) -> bool:
        """
        Informa se determinado elo pertence ao grupo.
        """

        normalized_rank = rank.strip().upper()

        return normalized_rank in self.current_ranks