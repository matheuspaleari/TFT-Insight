"""
Pesos padrão utilizados no cálculo de Performance.

Este módulo é mantido temporariamente para compatibilidade com
componentes que ainda importam METRIC_WEIGHTS diretamente.

Os pesos específicos de cada estágio competitivo ficam nos
BenchmarkProfiles.
"""

from src.performance_engine.models import MetricType


METRIC_WEIGHTS: dict[MetricType, float] = {
    MetricType.PLAYERS_ELIMINATED: 0.535683,
    MetricType.DAMAGE_TO_PLAYERS: 0.313694,
    MetricType.LEVEL: 0.107415,
    MetricType.CONSISTENCY: 0.043208,
}


__all__ = [
    "METRIC_WEIGHTS",
]