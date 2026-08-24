"""
Configuração dos estágios competitivos do TFT Insight.
"""

from .benchmark_group import BenchmarkGroup


STAGE_DISPLAY_NAMES: dict[str, str] = {
    "NOVICE": "Fundamentos",
    "INTERMEDIATE": "Competitivo",
    "ADVANCED": "Avançado",
    "EXPERT": "Especialista",
    "ELITE": "Elite",
    "TOP1": "Top 1 do Servidor",
}


BENCHMARK_GROUPS: tuple[BenchmarkGroup, ...] = (
    BenchmarkGroup(
        id="NOVICE",
        benchmark_id="novice",
        display_name=STAGE_DISPLAY_NAMES["NOVICE"],
        current_ranks=(
            "IRON",
            "BRONZE",
            "SILVER",
        ),
        target_stage="INTERMEDIATE",
    ),
    BenchmarkGroup(
        id="INTERMEDIATE",
        benchmark_id="intermediate",
        display_name=STAGE_DISPLAY_NAMES["INTERMEDIATE"],
        current_ranks=(
            "GOLD",
            "PLATINUM",
        ),
        target_stage="ADVANCED",
    ),
    BenchmarkGroup(
        id="ADVANCED",
        benchmark_id="advanced",
        display_name=STAGE_DISPLAY_NAMES["ADVANCED"],
        current_ranks=(
            "EMERALD",
            "DIAMOND",
        ),
        target_stage="EXPERT",
    ),
    BenchmarkGroup(
        id="EXPERT",
        benchmark_id="expert",
        display_name=STAGE_DISPLAY_NAMES["EXPERT"],
        current_ranks=(
            "MASTER",
        ),
        target_stage="ELITE",
    ),
    BenchmarkGroup(
        id="ELITE",
        benchmark_id="elite",
        display_name=STAGE_DISPLAY_NAMES["ELITE"],
        current_ranks=(
            "GRANDMASTER",
            "CHALLENGER",
        ),
        target_stage="TOP1",
    ),
)