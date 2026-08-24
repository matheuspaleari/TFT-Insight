"""
Teste manual do PerformanceEngine.

O benchmark é formado por jogadores Challenger.
O jogador analisado é pinador doss#000.

Execute na raiz do projeto:

python scripts/test_performance.py
"""

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
from src.performance_engine.engine import PerformanceEngine
from src.riot_client import RiotClient
from src.transformers.match_transformer import MatchTransformer


PLAYER_GAME_NAME = "pinador doss"
PLAYER_TAG_LINE = "000"

BENCHMARK_PLAYER_LIMIT = 5
BENCHMARK_MATCHES_PER_PLAYER = 10
PLAYER_MATCH_COUNT = 10


def main() -> None:
    riot_client = RiotClient()
    match_transformer = MatchTransformer()
    metrics_calculator = PlayerMetricsCalculator()
    benchmark_calculator = BenchmarkCalculator()

    collector = BenchmarkCollector(
        riot_client=riot_client,
        match_transformer=match_transformer,
        metrics_calculator=metrics_calculator,
        benchmark_calculator=benchmark_calculator,
    )

    print("Coletando jogadores Challenger...")

    challenger_players = collector.collect_players_metrics(
        player_limit=BENCHMARK_PLAYER_LIMIT,
        matches_per_player=BENCHMARK_MATCHES_PER_PLAYER,
    )

    if not challenger_players:
        raise RuntimeError(
            "Nenhum jogador Challenger foi coletado para o benchmark."
        )

    print(f"Jogadores coletados: {len(challenger_players)}")

    total_benchmark_matches = sum(
        metrics.general.matches_played
        for _, metrics in challenger_players
    )

    benchmark = benchmark_calculator.calculate(
        metrics=[
            metrics
            for _, metrics in challenger_players
        ],
        name="Teste Challenger BR",
        total_matches=total_benchmark_matches,
    )

    print("\nColetando partidas do jogador analisado...")

    account = riot_client.get_account(
        game_name=PLAYER_GAME_NAME,
        tag_line=PLAYER_TAG_LINE,
    )

    player_puuid = account["puuid"]

    match_ids = riot_client.get_match_ids(
        puuid=player_puuid,
        count=PLAYER_MATCH_COUNT,
    )

    if not match_ids:
        raise RuntimeError(
            "Nenhuma partida foi encontrada para o jogador analisado."
        )

    print(f"Partidas encontradas: {len(match_ids)}")

    transformed_matches = []

    for index, match_id in enumerate(match_ids, start=1):
        print(
            f"Processando partida {index}/{len(match_ids)}: "
            f"{match_id}"
        )

        match_data = riot_client.get_match_details(
            match_id=match_id,
        )

        transformed_match = match_transformer.transform(
            match_data,
            player_puuid,
        )

        transformed_matches.append(transformed_match)

    player_metrics = metrics_calculator.calculate(
        matches=transformed_matches,
    )

    player_name = (
        f'{account["gameName"]}#{account["tagLine"]}'
    )

    performance = PerformanceEngine.calculate(
        player_metrics=player_metrics,
        benchmark=benchmark,
    )

    potential_score = (
        f"{performance.potential_score:.1f}"
        if performance.potential_score is not None
        else "N/A"
    )

    print()
    print("=" * 80)
    print("PERFORMANCE ANALYSIS")
    print("=" * 80)

    print(f"Player            : {player_name}")
    print(f"Overall Score     : {performance.score:.1f}")
    print(f"Status            : {performance.status}")
    print(f"Potential Score   : {potential_score}")
    print(f"Benchmark         : {performance.benchmark_name}")
    print(f"Matches Analyzed  : {performance.matches_analyzed}")

    print()
    print("=" * 80)
    print("METRIC EVALUATIONS")
    print("=" * 80)

    for evaluation in performance.evaluations:
        print()
        print(f"Metric            : {evaluation.metric.value}")
        print(f"Player Value      : {evaluation.player_value:.2f}")
        print(
            f"Benchmark Mean    : "
            f"{evaluation.benchmark_metric.mean:.2f}"
        )
        print(
            f"Benchmark Std Dev : "
            f"{evaluation.benchmark_metric.standard_deviation:.2f}"
        )
        print(f"Score             : {evaluation.score:.2f}")
        print(f"Weight            : {evaluation.weight:.6f}")
        print("-" * 80)

    print()
    print("=" * 80)
    print("TOP PRIORITIES")
    print("=" * 80)

    if not performance.priorities:
        print("Nenhuma prioridade foi gerada.")

    for priority in performance.priorities:
        print()
        print(f"#{priority.rank} - {priority.title}")
        print(f"Current Score : {priority.current_score:.2f}")
        print(f"Gap           : {priority.gap:.2f}")
        print(f"Impact        : {priority.impact:.2f}")
        print(f"Confidence    : {priority.confidence:.2f}")

        print("\nDescription:")
        print(priority.description)

        print("\nRecommendations:")

        if not priority.recommendations:
            print("  Nenhuma recomendação cadastrada.")
        else:
            for recommendation in priority.recommendations:
                print(f"  • {recommendation}")

        print("-" * 80)


if __name__ == "__main__":
    main()