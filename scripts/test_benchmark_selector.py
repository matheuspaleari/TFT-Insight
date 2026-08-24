from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.benchmark import BenchmarkSelector


TEST_RANKS = (
    "IRON",
    "BRONZE",
    "SILVER",
    "GOLD",
    "PLATINUM",
    "EMERALD",
    "DIAMOND",
    "MASTER",
    "GRANDMASTER",
    "CHALLENGER",
)


def main() -> None:
    print()
    print("=" * 80)
    print("TFT INSIGHT - BENCHMARK SELECTOR")
    print("=" * 80)

    for rank in TEST_RANKS:
        group = BenchmarkSelector.from_rank(
            rank
        )

        target_name = (
            BenchmarkSelector.get_target_display_name(
                group
            )
        )

        print()
        print(f"Elo atual       : {rank}")
        print(f"Grupo interno   : {group.id}")
        print(f"Estágio atual   : {group.display_name}")
        print(f"Benchmark       : {group.benchmark_id}")
        print(f"Objetivo atual  : {target_name}")
        print("-" * 80)

    master_group = BenchmarkSelector.from_rank(
        "master"
    )

    if master_group.id != "EXPERT":
        raise AssertionError(
            "MASTER deveria pertencer ao grupo EXPERT."
        )

    if (
        BenchmarkSelector.get_target_display_name(
            master_group
        )
        != "Elite"
    ):
        raise AssertionError(
            "O objetivo do grupo EXPERT deveria ser Elite."
        )

    challenger_group = (
        BenchmarkSelector.from_rank(
            "challenger"
        )
    )

    if (
        BenchmarkSelector.get_target_display_name(
            challenger_group
        )
        != "Top 1 do Servidor"
    ):
        raise AssertionError(
            "O objetivo do Challenger deveria ser "
            "Top 1 do Servidor."
        )

    print()
    print("✓ Seleção de estágios validada com sucesso.")


if __name__ == "__main__":
    main()