"""
Perfis de comportamento dos benchmarks.
"""

from src.performance_engine.models import MetricType

from .benchmark_profile import BenchmarkProfile


DEFAULT_PERFORMANCE_WEIGHTS: dict[
    MetricType,
    float,
] = {
    MetricType.PLAYERS_ELIMINATED: 0.535683,
    MetricType.DAMAGE_TO_PLAYERS: 0.313694,
    MetricType.LEVEL: 0.107415,
    MetricType.CONSISTENCY: 0.043208,
}


def _default_weights() -> dict[MetricType, float]:
    return dict(DEFAULT_PERFORMANCE_WEIGHTS)


BENCHMARK_PROFILES: dict[str, BenchmarkProfile] = {
    # Compatibilidade temporária com o benchmark atual.
    "challenger_br": BenchmarkProfile(
        id="challenger_br",
        performance_weights=_default_weights(),
    ),

    "novice": BenchmarkProfile(
        id="novice",
        performance_weights=_default_weights(),
    ),
    "intermediate": BenchmarkProfile(
        id="intermediate",
        performance_weights=_default_weights(),
    ),
    "advanced": BenchmarkProfile(
        id="advanced",
        performance_weights=_default_weights(),
    ),
    "expert": BenchmarkProfile(
        id="expert",
        performance_weights=_default_weights(),
    ),
    "elite": BenchmarkProfile(
        id="elite",
        performance_weights=_default_weights(),
    ),
}


__all__ = [
    "BENCHMARK_PROFILES",
    "DEFAULT_PERFORMANCE_WEIGHTS",
]