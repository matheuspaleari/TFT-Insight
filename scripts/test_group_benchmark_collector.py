"""
Teste leve da integração do BenchmarkCollector por grupo.

Por padrão, usa uma configuração temporária pequena:
2 jogadores válidos e 3 partidas por jogador.
Isso evita disparar a coleta completa de 50 x 30 no primeiro teste.
"""

from dataclasses import replace
from pathlib import Path
import sys

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

load_dotenv(
    PROJECT_ROOT / ".env"
)


import src.benchmark.group_configuration as group_module
from src.benchmark import LeaguePlayerProvider
from src.performance_engine.calculators import (
    BenchmarkCalculator,
    PlayerMetricsCalculator,
)
from src.performance_engine.collectors import (
    BenchmarkCollector,
)
from src.riot_client import RiotClient
from src.transformers.match_transformer import (
    MatchTransformer,
)


def main() -> None:
    benchmark_id = "intermediate"

    original = (
        group_module
        .BENCHMARK_GROUP_CONFIGURATIONS[
            benchmark_id
        ]
    )

    test_configuration = replace(
        original,
        target_valid_players=2,
        matches_per_player=3,
        candidate_multiplier=2.0,
        sampling_rules=tuple(
            replace(
                rule,
                target_players=1,
            )
            for rule in original.sampling_rules
        ),
    )

    group_module.BENCHMARK_GROUP_CONFIGURATIONS[
        benchmark_id
    ] = test_configuration

    try:
        riot_client = RiotClient()

        collector = BenchmarkCollector(
            riot_client=riot_client,
            match_transformer=(
                MatchTransformer()
            ),
            metrics_calculator=(
                PlayerMetricsCalculator()
            ),
            benchmark_calculator=(
                BenchmarkCalculator()
            ),
            player_provider=(
                LeaguePlayerProvider(
                    riot_client=riot_client,
                )
            ),
        )

        benchmark = collector.collect(
            benchmark_id=benchmark_id,
            minimum_valid_matches=2,
        )

        print()
        print("=" * 80)
        print("TFT INSIGHT - TESTE DO GROUP BENCHMARK COLLECTOR")
        print("=" * 80)
        print(
            f"Nome              : "
            f"{benchmark.name}"
        )
        print(
            f"Jogadores         : "
            f"{benchmark.players_analyzed}"
        )
        print(
            f"Partidas          : "
            f"{benchmark.matches_analyzed}"
        )
        print(
            f"Nível médio       : "
            f"{benchmark.average_level.mean}"
        )
        print()
        print(
            "✓ BenchmarkCollector validado com sucesso."
        )

    finally:
        group_module.BENCHMARK_GROUP_CONFIGURATIONS[
            benchmark_id
        ] = original


if __name__ == "__main__":
    main()
