from pathlib import Path
import sys
from time import perf_counter

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")


from src.inspector import InspectorEngine
from src.learning import (
    SkillMappingService,
)
from src.services import PlayerAnalysisService


def print_separator(
    character: str = "=",
) -> None:
    print(character * 80)


def main() -> None:
    start = perf_counter()

    analysis = PlayerAnalysisService().analyze(
        game_name="Pinador Doss",
        tag_line="000",
        match_count=10,
        use_cache=True,
    )

    assessments = SkillMappingService.assess(
        performance=analysis.performance,
    )

    inspections = InspectorEngine.inspect_all(
        assessments=assessments,
        performance=analysis.performance,
    )

    print()
    print_separator()
    print("TFT INSIGHT - INSPECTOR")
    print_separator()

    print()
    print(f"Jogador   : {analysis.riot_id}")
    print(
        f"Benchmark : "
        f"{analysis.benchmark_id}"
    )

    for inspection in inspections:
        print()
        print_separator()
        print(
            inspection.skill_title.upper()
        )
        print_separator()

        print()
        print(
            f"Score interno : "
            f"{inspection.score:.1f}"
        )
        print(
            f"Confiança     : "
            f"{inspection.confidence:.1f}%"
        )

        print()
        print("DIAGNÓSTICO")
        print("-" * 80)
        print(inspection.summary)

        if inspection.metric_inspections:
            print()
            print("EVIDÊNCIAS")
            print("-" * 80)

        for metric in (
            inspection.metric_inspections
        ):
            print()
            print(
                f"Métrica             : "
                f"{metric.metric_id}"
            )
            print(
                f"Jogador             : "
                f"{metric.player_value:.2f}"
            )
            print(
                f"Média da referência : "
                f"{metric.benchmark_mean:.2f}"
            )
            print(
                f"Mediana             : "
                f"{metric.benchmark_median:.2f}"
            )
            print(
                f"Q1 / Q3             : "
                f"{metric.benchmark_first_quartile:.2f}"
                f" / "
                f"{metric.benchmark_third_quartile:.2f}"
            )
            print(
                f"Desvio padrão       : "
                f"{metric.benchmark_standard_deviation:.2f}"
            )
            print(
                f"Diferença da média  : "
                f"{metric.difference_from_mean:+.2f}"
            )
            print(
                f"Z-Score interpretado: "
                f"{metric.z_score:+.2f}"
            )
            print(
                f"Percentil           : "
                f"{metric.percentile:.2f}%"
            )
            print(
                f"Peso                : "
                f"{metric.weight:.6f}"
            )
            print(
                f"Impacto ponderado   : "
                f"{metric.weighted_impact:.2f}"
            )
            print(
                f"Posição             : "
                f"{metric.position_label}"
            )

        if inspection.limitations:
            print()
            print("LIMITAÇÕES")
            print("-" * 80)

            for limitation in (
                inspection.limitations
            ):
                print(f"• {limitation}")

    print()
    print_separator()
    print(
        f"Tempo total: "
        f"{perf_counter() - start:.2f}s"
    )
    print_separator()


if __name__ == "__main__":
    main()