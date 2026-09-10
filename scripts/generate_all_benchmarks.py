"""
Gera e persiste todos os benchmarks competitivos do TFT Insight.

Uso padrão:

    python scripts/generate_all_benchmarks.py

Gerar somente alguns grupos:

    python scripts/generate_all_benchmarks.py advanced expert

Por padrão, aceita jogadores com pelo menos 5 partidas válidas do Set alvo.

Alterar o mínimo manualmente:

    python scripts/generate_all_benchmarks.py --minimum-valid-matches 10
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

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


from src.benchmark import (
    BENCHMARK_GROUP_CONFIGURATIONS,
    LeaguePlayerProvider,
)
from src.performance_engine.calculators import (
    BenchmarkCalculator,
    PlayerMetricsCalculator,
)
from src.performance_engine.collectors import (
    BenchmarkCollector,
)
from src.performance_engine.collectors.benchmark_collector import (
    DEFAULT_MINIMUM_VALID_MATCHES,
)
from src.performance_engine.engine import (
    BenchmarkEngine,
)
from src.riot_client import RiotClient
from src.transformers.match_transformer import (
    MatchTransformer,
)


DEFAULT_BENCHMARK_IDS = (
    "novice",
    "intermediate",
    "advanced",
    "expert",
    "elite",
)


def build_engine() -> BenchmarkEngine:
    """
    Monta todas as dependências necessárias para geração.
    """

    riot_client = RiotClient()

    collector = BenchmarkCollector(
        riot_client=riot_client,
        match_transformer=MatchTransformer(),
        metrics_calculator=PlayerMetricsCalculator(),
        benchmark_calculator=BenchmarkCalculator(),
        player_provider=LeaguePlayerProvider(
            riot_client=riot_client,
        ),
    )

    return BenchmarkEngine(
        collector=collector,
    )


def parse_arguments() -> argparse.Namespace:
    """
    Lê os argumentos informados no terminal.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Gera os benchmarks competitivos do TFT Insight."
        )
    )

    parser.add_argument(
        "benchmark_ids",
        nargs="*",
        choices=DEFAULT_BENCHMARK_IDS,
        help=(
            "Benchmarks que serão gerados. "
            "Quando omitido, gera todos."
        ),
    )

    parser.add_argument(
        "--minimum-valid-matches",
        type=int,
        default=DEFAULT_MINIMUM_VALID_MATCHES,
        help=(
            "Quantidade mínima de partidas válidas exigida "
            "por jogador. Padrão: "
            f"{DEFAULT_MINIMUM_VALID_MATCHES}."
        ),
    )

    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help=(
            "Continua para o próximo benchmark caso algum "
            "grupo apresente erro."
        ),
    )

    return parser.parse_args()


def validate_arguments(
    *,
    minimum_valid_matches: int | None,
) -> None:
    """
    Valida argumentos que dependem das configurações dos grupos.
    """

    if (
        minimum_valid_matches is not None
        and minimum_valid_matches < 1
    ):
        raise ValueError(
            "--minimum-valid-matches deve ser maior que zero."
        )

    smallest_configured_sample = min(
        configuration.matches_per_player
        for configuration
        in BENCHMARK_GROUP_CONFIGURATIONS.values()
    )

    if minimum_valid_matches > smallest_configured_sample:
        raise ValueError(
            "--minimum-valid-matches não pode ser maior "
            "que a quantidade de partidas configurada por jogador."
        )


def generate_benchmark(
    *,
    engine: BenchmarkEngine,
    benchmark_id: str,
    minimum_valid_matches: int | None,
) -> tuple[bool, float, str]:
    """
    Gera um benchmark e retorna status, tempo e mensagem.
    """

    started_at = time.monotonic()

    try:
        benchmark = engine.refresh(
            benchmark_id=benchmark_id,
            minimum_valid_matches=(
                minimum_valid_matches
            ),
        )

    except (
        RuntimeError,
        ValueError,
        FileNotFoundError,
    ) as error:
        elapsed = time.monotonic() - started_at

        return (
            False,
            elapsed,
            str(error),
        )

    elapsed = time.monotonic() - started_at

    return (
        True,
        elapsed,
        (
            f"{benchmark.players_analyzed} jogadores · "
            f"{benchmark.matches_analyzed} partidas"
        ),
    )


def print_plan(
    benchmark_ids: tuple[str, ...],
    minimum_valid_matches: int | None,
) -> None:
    """
    Exibe o plano antes de iniciar uma coleta longa.
    """

    print()
    print("=" * 80)
    print("TFT INSIGHT - GERADOR DE BENCHMARKS")
    print("=" * 80)

    for benchmark_id in benchmark_ids:
        configuration = (
            BENCHMARK_GROUP_CONFIGURATIONS[
                benchmark_id
            ]
        )

        required_matches = (
            DEFAULT_MINIMUM_VALID_MATCHES
            if minimum_valid_matches is None
            else minimum_valid_matches
        )

        print()
        print(
            f"{benchmark_id.upper():<14} "
            f"{configuration.display_name}"
        )
        print(
            f"  Jogadores válidos : "
            f"{configuration.target_valid_players}"
        )
        print(
            f"  Partidas/jogador  : "
            f"{configuration.matches_per_player}"
        )
        print(
            f"  Mínimo válido     : "
            f"{required_matches}"
        )
        print(
            f"  Candidatos alvo   : "
            f"{configuration.candidate_limit}"
        )

    print()
    print(
        "Os arquivos serão salvos em: "
        "data/benchmark/<benchmark_id>.json"
    )
    print("=" * 80)


def print_summary(
    results: list[
        tuple[str, bool, float, str]
    ],
    total_elapsed: float,
) -> None:
    """
    Exibe o resumo final da execução.
    """

    print()
    print("=" * 80)
    print("RESUMO DA GERAÇÃO")
    print("=" * 80)

    for (
        benchmark_id,
        success,
        elapsed,
        message,
    ) in results:
        status = (
            "SUCESSO"
            if success
            else "ERRO"
        )

        print(
            f"{benchmark_id:<14} "
            f"{status:<8} "
            f"{elapsed:>9.2f}s  "
            f"{message}"
        )

    successful = sum(
        1
        for _, success, _, _ in results
        if success
    )

    failed = len(results) - successful

    print("-" * 80)
    print(
        f"Concluídos : {successful}"
    )
    print(
        f"Falhas     : {failed}"
    )
    print(
        f"Tempo total: {total_elapsed:.2f}s"
    )
    print("=" * 80)


def main() -> None:
    args = parse_arguments()

    validate_arguments(
        minimum_valid_matches=(
            args.minimum_valid_matches
        ),
    )

    benchmark_ids = tuple(
        args.benchmark_ids
        or DEFAULT_BENCHMARK_IDS
    )

    print_plan(
        benchmark_ids=benchmark_ids,
        minimum_valid_matches=(
            args.minimum_valid_matches
        ),
    )

    engine = build_engine()

    results: list[
        tuple[str, bool, float, str]
    ] = []

    total_started_at = time.monotonic()

    for index, benchmark_id in enumerate(
        benchmark_ids,
        start=1,
    ):
        print()
        print("#" * 80)
        print(
            f"[{index}/{len(benchmark_ids)}] "
            f"GERANDO {benchmark_id.upper()}"
        )
        print("#" * 80)

        (
            success,
            elapsed,
            message,
        ) = generate_benchmark(
            engine=engine,
            benchmark_id=benchmark_id,
            minimum_valid_matches=(
                args.minimum_valid_matches
            ),
        )

        results.append(
            (
                benchmark_id,
                success,
                elapsed,
                message,
            )
        )

        if not success:
            print()
            print(
                f"Falha ao gerar '{benchmark_id}': "
                f"{message}"
            )

            if not args.continue_on_error:
                print()
                print(
                    "Execução interrompida. Use "
                    "--continue-on-error para continuar "
                    "mesmo quando um grupo falhar."
                )
                break

    total_elapsed = (
        time.monotonic()
        - total_started_at
    )

    print_summary(
        results=results,
        total_elapsed=total_elapsed,
    )

    if any(
        not success
        for _, success, _, _ in results
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
