from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.benchmark import (
    BENCHMARK_GROUP_CONFIGURATIONS,
)


def main() -> None:
    print()
    print("=" * 80)
    print("TFT INSIGHT - BENCHMARK GROUP CONFIGURATION")
    print("=" * 80)

    for benchmark_id, configuration in (
        BENCHMARK_GROUP_CONFIGURATIONS.items()
    ):
        print()
        print(f"Benchmark          : {benchmark_id}")
        print(
            f"Nome               : "
            f"{configuration.display_name}"
        )
        print(
            f"Jogadores válidos  : "
            f"{configuration.target_valid_players}"
        )
        print(
            f"Partidas/jogador   : "
            f"{configuration.matches_per_player}"
        )
        print(
            f"Candidatos estimados: "
            f"{configuration.candidate_limit}"
        )

        for rule in configuration.sampling_rules:
            divisions = (
                ", ".join(rule.divisions)
                if rule.divisions
                else "liga apex"
            )

            print(
                f"  - {rule.tier:<12} "
                f"{rule.target_players:>2} jogadores "
                f"({divisions})"
            )

        if (
            sum(
                rule.target_players
                for rule in configuration.sampling_rules
            )
            != configuration.target_valid_players
        ):
            raise AssertionError(
                f"A distribuição de {benchmark_id} "
                "não soma a meta configurada."
            )

    print()
    print("✓ Configurações validadas com sucesso.")


if __name__ == "__main__":
    main()