from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.benchmark import (
    BenchmarkContextBuilder,
)


def main():

    for rank in (
        "IRON",
        "GOLD",
        "MASTER",
        "CHALLENGER",
    ):

        context = (
            BenchmarkContextBuilder.build(
                current_rank=rank,
            )
        )

        print()

        print("=" * 60)

        print(f"Riot Rank     : {rank}")

        print(
            f"Estágio       : "
            f"{context.group.display_name}"
        )

        print(
            f"Objetivo      : "
            f"{context.group.target_stage}"
        )

        print(
            f"Benchmark     : "
            f"{context.benchmark_id}"
        )

        print(
            f"Profile       : "
            f"{context.profile.id}"
        )


if __name__ == "__main__":
    main()