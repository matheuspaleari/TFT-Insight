"""
Perfis de configuração dos benchmarks.
"""

from .benchmark_profile import BenchmarkProfile
from .benchmark_profiles import (
    BENCHMARK_PROFILES,
    DEFAULT_PERFORMANCE_WEIGHTS,
)
from .profile_selector import BenchmarkProfileSelector


__all__ = [
    "BENCHMARK_PROFILES",
    "DEFAULT_PERFORMANCE_WEIGHTS",
    "BenchmarkProfile",
    "BenchmarkProfileSelector",
]