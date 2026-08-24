"""
Serviço responsável por selecionar o estágio competitivo
correspondente ao elo atual do jogador.
"""

from .benchmark_group import BenchmarkGroup
from .benchmark_groups import (
    BENCHMARK_GROUPS,
    STAGE_DISPLAY_NAMES,
)


class BenchmarkSelector:
    """
    Centraliza a relação entre os elos da Riot
    e os estágios competitivos do TFT Insight.
    """

    @classmethod
    def from_rank(
        cls,
        rank: str,
    ) -> BenchmarkGroup:
        """
        Retorna o grupo correspondente ao elo informado.
        """

        normalized_rank = cls._normalize_rank(
            rank
        )

        for group in BENCHMARK_GROUPS:
            if group.contains_rank(
                normalized_rank
            ):
                return group

        raise ValueError(
            "Não existe estágio competitivo configurado "
            f"para o elo {normalized_rank!r}."
        )

    @staticmethod
    def get_stage_display_name(
        stage_id: str,
    ) -> str:
        """
        Retorna o nome amigável de um estágio.
        """

        normalized_stage_id = (
            stage_id.strip().upper()
        )

        display_name = STAGE_DISPLAY_NAMES.get(
            normalized_stage_id
        )

        if display_name is None:
            raise ValueError(
                "Estágio competitivo desconhecido: "
                f"{normalized_stage_id!r}."
            )

        return display_name

    @classmethod
    def get_target_display_name(
        cls,
        group: BenchmarkGroup,
    ) -> str:
        """
        Retorna o nome amigável do objetivo atual do grupo.
        """

        return cls.get_stage_display_name(
            group.target_stage
        )

    @staticmethod
    def _normalize_rank(
        rank: str,
    ) -> str:
        normalized_rank = rank.strip().upper()

        if not normalized_rank:
            raise ValueError(
                "O elo do jogador deve ser informado."
            )

        return normalized_rank