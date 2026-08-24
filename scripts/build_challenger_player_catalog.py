from pathlib import Path
import sys

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from src.benchmark_intelligence import (
    BenchmarkIntelligenceService,
)


def main() -> None:
    service = (
        BenchmarkIntelligenceService(
            project_root=PROJECT_ROOT
        )
    )

    catalog = (
        service.rebuild_player_catalog()
    )

    print("=" * 88)
    print(
        "TFT INSIGHT - CHALLENGER PLAYER CATALOG"
    )
    print("=" * 88)
    print(
        f"Players resolved : {len(catalog)}"
    )
    print(
        "Source           : local cached match payloads"
    )
    print(
        "Riot API calls   : 0"
    )
    print()
    print(
        "✓ Challenger player catalog generated."
    )


if __name__ == "__main__":
    main()
