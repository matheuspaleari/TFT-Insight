"""
Teste de integração da v1 do TFT Insight.
"""

from pathlib import Path
import sys

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")


from src.services import PlayerAnalysisService


def main() -> None:
    service = PlayerAnalysisService()

    performance = service.analyze(
        game_name="Pinador Doss",
        tag_line="000",
        benchmark_id="challenger_br",
        match_count=10,
    )

    print()
    print("=" * 80)
    print("TFT INSIGHT V1")
    print("=" * 80)

    print(f"Score: {performance.score:.1f}")
    print(f"Status: {performance.status}")
    print(f"Potential score: {performance.potential_score}")
    print(f"Benchmark: {performance.benchmark_name}")
    print(f"Partidas: {performance.matches_analyzed}")

    print()
    print("PRIORIDADES")
    print("-" * 80)

    for priority in performance.priorities:
        print(
            f"#{priority.rank} "
            f"{priority.title} "
            f"(impacto: {priority.impact:.2f})"
        )

        print(priority.description)

        for recommendation in priority.recommendations:
            print(f"• {recommendation}")

        print("-" * 80)


if __name__ == "__main__":
    main()