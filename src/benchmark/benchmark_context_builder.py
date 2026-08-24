"""
Constrói o contexto competitivo do jogador.
"""

from src.benchmark_profiles import (
    BenchmarkProfileSelector,
)

from .benchmark_context import BenchmarkContext
from .benchmark_selector import BenchmarkSelector


class BenchmarkContextBuilder:

    @classmethod
    def build(
        cls,
        *,
        current_rank: str,
    ) -> BenchmarkContext:

        group = BenchmarkSelector.from_rank(
            current_rank
        )

        profile = (
            BenchmarkProfileSelector.get(
                group.benchmark_id
            )
        )

        # Cada grupo competitivo usa seu próprio benchmark persistido.
        benchmark_id = group.benchmark_id

        return BenchmarkContext(
            current_rank=current_rank,
            group=group,
            profile=profile,
            benchmark_id=benchmark_id,
        )