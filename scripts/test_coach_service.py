from pathlib import Path
import sys

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.coach import CoachService
from src.services import PlayerAnalysisService


def main() -> None:
    analysis_service = PlayerAnalysisService()
    coach_service = CoachService()

    performance = analysis_service.analyze(
        game_name="Pinador Doss",
        tag_line="000",
        benchmark_id="challenger_br",
        match_count=10,
    )

    response = coach_service.generate(
        performance=performance,
    )

    training_plan = response.training_plan

    print()
    print("=" * 80)
    print("TFT INSIGHT - COACH SESSION")
    print("=" * 80)

    print()
    print("RESUMO")
    print("-" * 80)
    print(response.summary)

    print()
    print("DIAGNÓSTICO")
    print("-" * 80)
    print(training_plan.diagnosis)

    print()
    print(
        f"OBJETIVO DAS PRÓXIMAS "
        f"{training_plan.games_target} PARTIDAS"
    )
    print("-" * 80)
    print(training_plan.objective)

    print()
    print("AÇÕES PRINCIPAIS")
    print("-" * 80)

    for action in training_plan.actions:
        print(f"• {action}")

    print()
    print("CHECKLIST DURANTE A PARTIDA")
    print("-" * 80)

    for item in training_plan.checklist:
        print(f"□ {item}")

    print()
    print("ERROS COMUNS")
    print("-" * 80)

    for mistake in training_plan.common_mistakes:
        print(f"• {mistake}")

    print()
    print("CONCEITO PARA ESTUDAR")
    print("-" * 80)
    print(training_plan.learning_title)
    print()
    print(training_plan.learning_content)

    print()
    print("EVOLUÇÃO ESPERADA")
    print("-" * 80)

    for improvement in training_plan.expected_improvements:
        print(f"↑ {improvement}")

    print()
    print("MÉTRICAS ACOMPANHADAS")
    print("-" * 80)

    for metric_id in training_plan.monitored_metrics:
        print(f"• {metric_id}")

    if response.raw_text:
        print()
        print("RESPOSTA NATURAL")
        print("-" * 80)
        print(response.raw_text)


if __name__ == "__main__":
    main()