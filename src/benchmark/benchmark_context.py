"""
Contexto competitivo do jogador.
"""

from dataclasses import dataclass

from src.benchmark_profiles import BenchmarkProfile

from .benchmark_group import BenchmarkGroup


@dataclass(slots=True, frozen=True)
class BenchmarkContext:
    """
    Reúne todas as informações necessárias para que
    os Engines trabalhem sem conhecer a Riot API.
    """

    current_rank: str

    group: BenchmarkGroup

    profile: BenchmarkProfile

    benchmark_id: str