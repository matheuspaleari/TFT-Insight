"""
Seletor dos perfis de benchmark.
"""

from .benchmark_profile import BenchmarkProfile
from .benchmark_profiles import BENCHMARK_PROFILES


class BenchmarkProfileSelector:
    """
    Retorna o perfil associado a um benchmark.
    """

    @staticmethod
    def get(
        benchmark_id: str,
    ) -> BenchmarkProfile:
        normalized_id = benchmark_id.strip().lower()

        if not normalized_id:
            raise ValueError(
                "O identificador do benchmark "
                "deve ser informado."
            )

        profile = BENCHMARK_PROFILES.get(
            normalized_id
        )

        if profile is None:
            raise ValueError(
                "Não existe perfil configurado para "
                f"o benchmark {normalized_id!r}."
            )

        return profile