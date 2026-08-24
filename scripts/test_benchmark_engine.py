from pathlib import Path
import sys

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.performance_engine.calculators import (
    BenchmarkCalculator,
    PlayerMetricsCalculator,
)
from src.performance_engine.collectors import BenchmarkCollector
from src.performance_engine.engine import BenchmarkEngine
from src.riot_client import RiotClient
from src.transformers.match_transformer import MatchTransformer


def main() -> None:
    riot_client = RiotClient()

    collector = BenchmarkCollector(
        riot_client=riot_client,
        match_transformer=MatchTransformer(),
        metrics_calculator=PlayerMetricsCalculator(),
        benchmark_calculator=BenchmarkCalculator(),
    )

    benchmark_engine = BenchmarkEngine(
        collector=collector,
    )

    benchmark = benchmark_engine.load_or_collect(
        benchmark_id="challenger_br",
        player_limit=10,
        matches_per_player=10,
    )

    print()
    print("=" * 60)
    print("BENCHMARK")
    print("=" * 60)
    print(f"Nome: {benchmark.name}")
    print(f"Jogadores analisados: {benchmark.players_analyzed}")
    print(f"Partidas analisadas: {benchmark.matches_analyzed}")

    print()
    print(
        "Benchmarks disponíveis:",
        benchmark_engine.list_available(),
    )


if __name__ == "__main__":
    main()