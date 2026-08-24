from pathlib import Path
import sys

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")


from src.learning import SkillMappingService
from src.services import PlayerAnalysisService


def main() -> None:
    analysis_service = PlayerAnalysisService()

    performance = analysis_service.analyze(
        game_name="Pinador Doss",
        tag_line="000",
        benchmark_id="challenger_br",
        match_count=10,
    )

    assessments = SkillMappingService.assess(
        performance=performance,
    )

    print()
    print("=" * 80)
    print("TFT INSIGHT - SKILL MAPPING")
    print("=" * 80)

    for assessment in assessments:
        print()
        print(assessment.skill.title)
        print("-" * 80)
        print(f"Score      : {assessment.score:.1f}")
        print(f"Nível      : {assessment.level.name}")
        print(f"Visual     : {assessment.stars}")
        print(f"Confiança  : {assessment.confidence:.1f}%")

        if assessment.evidence_metric_ids:
            print("Evidências:")

            for metric_id in assessment.evidence_metric_ids:
                print(f"  • {metric_id}")
        else:
            print("Evidências: nenhuma evidência direta")

        print("Limitações:")

        for limitation in assessment.limitations:
            print(f"  • {limitation}")


if __name__ == "__main__":
    main()