from pathlib import Path
import sys
from time import perf_counter

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.learning import SkillMappingService
from src.learning.services import LearningEngine
from src.services import PlayerAnalysisService


def log(message: str) -> float:
    print()
    print("=" * 80)
    print(message)
    print("=" * 80)
    return perf_counter()


def elapsed(start: float) -> None:
    print(f"✓ Concluído em {perf_counter() - start:.2f}s")


def main() -> None:
    total_start = perf_counter()

    analysis_service = PlayerAnalysisService()

    print()
    print("=" * 80)
    print("TFT INSIGHT - LEARNING ENGINE")
    print("=" * 80)

    # ------------------------------------------------------------------

    start = log("1. Analisando jogador (Riot API + Performance Engine)")

    performance = analysis_service.analyze(
        game_name="Pinador Doss",
        tag_line="000",
        benchmark_id="challenger_br",
        match_count=10,
    )

    elapsed(start)

    # ------------------------------------------------------------------

    start = log("2. Mapeando Skills")

    assessments = SkillMappingService.assess(
        performance=performance,
    )

    elapsed(start)

    # ------------------------------------------------------------------

    start = log("3. Executando Learning Engine")

    recommendation = LearningEngine.recommend(
        assessments=assessments,
    )

    elapsed(start)

    # ------------------------------------------------------------------

    selected = recommendation.assessment

    print()
    print("=" * 80)
    print("RESULTADO")
    print("=" * 80)

    print(f"Skill escolhida : {recommendation.skill.title}")
    print(f"Score           : {selected.score:.1f}")
    print(f"Nível           : {selected.level.name}")
    print(f"Visual          : {selected.stars}")
    print(f"Confiança       : {recommendation.confidence:.1f}%")

    print()
    print("Motivo")
    print("-" * 80)
    print(recommendation.reason)

    print()
    print("Evidências")
    print("-" * 80)

    if selected.evidence_metric_ids:
        for metric in selected.evidence_metric_ids:
            print(f"• {metric}")
    else:
        print("Nenhuma.")

    print()
    print("Limitações")
    print("-" * 80)

    if selected.limitations:
        for limitation in selected.limitations:
            print(f"• {limitation}")
    else:
        print("Nenhuma.")

    print()
    print("=" * 80)
    print(f"Tempo total: {perf_counter() - total_start:.2f}s")
    print("=" * 80)


if __name__ == "__main__":
    main()