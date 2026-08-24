"""
Estágios competitivos e seleção de benchmarks do TFT Insight.
"""

from .benchmark_group import BenchmarkGroup
from .benchmark_groups import (
    BENCHMARK_GROUPS,
    STAGE_DISPLAY_NAMES,
)
from .benchmark_selector import BenchmarkSelector
from .benchmark_context import BenchmarkContext
from .benchmark_context_builder import (
    BenchmarkContextBuilder,
)

from .group_configuration import (
    BENCHMARK_GROUP_CONFIGURATIONS,
    BenchmarkGroupConfiguration,
    TierSamplingRule,
    get_benchmark_group_configuration,
)
from .providers import LeaguePlayerProvider
from .models import LeaguePlayer
from .player_catalog import (
    BenchmarkPlayerCatalogEntry,
    BenchmarkPlayerCatalogRepository,
    metrics_to_dict,
    utc_now_iso,
)
from .rank_validation_service import BenchmarkRankValidationService
from .competitive_spectrum_engine import (
    CompetitiveSpectrumEngine,
    CompetitiveSpectrumResult,
    SpectrumMetricProfile,
)

__all__ = [
    "BENCHMARK_GROUPS",
    "STAGE_DISPLAY_NAMES",
    "BenchmarkGroup",
    "BenchmarkSelector",
    "BenchmarkContext",
    "BenchmarkContextBuilder",
    "BENCHMARK_GROUP_CONFIGURATIONS",
    "BenchmarkGroupConfiguration",
    "TierSamplingRule",
    "get_benchmark_group_configuration",
    "LeaguePlayerProvider",
    "LeaguePlayer",
    "BenchmarkPlayerCatalogEntry",
    "BenchmarkPlayerCatalogRepository",
    "BenchmarkRankValidationService",
    "CompetitiveSpectrumEngine",
    "CompetitiveSpectrumResult",
    "SpectrumMetricProfile",
    "metrics_to_dict",
    "utc_now_iso",
]