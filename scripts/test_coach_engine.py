from pathlib import Path
import sys
from time import perf_counter

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")


from src.coach import CoachEngine


def main() -> None:
    start = perf_counter()

    engine = CoachEngine()

    print()
    print("=" * 80)
    print("TFT INSIGHT - COACH ENGINE")
    print("=" * 80)

    report = engine.analyze(
        game_name="Pinador Doss",
        tag_line="000",
        match_count=10,
        use_cache=True,
        mission_games_target=5,
    )

    mission = report.mission
    recommendation = report.learning_recommendation

    inspection = report.current_inspection

    print()
    print("JOGADOR")
    print("-" * 80)
    print(report.riot_id)

    print()
    print("PERFORMANCE")
    print("-" * 80)
    print(f"Score: {report.performance.score:.1f}")
    print(
        f"Partidas: "
        f"{report.performance.matches_analyzed}"
    )

    print()
    print("FOCO ATUAL")
    print("-" * 80)
    print(recommendation.skill.title)
    print(
        f"Confiança: "
        f"{recommendation.confidence:.1f}%"
    )

    print()
    print("INSPECTOR")
    print("-" * 80)
    print(inspection.summary)

    for metric in inspection.metric_inspections:
        print()
        print(f"Métrica    : {metric.metric_id}")
        print(f"Jogador    : {metric.player_value:.2f}")
        print(f"Referência : {metric.benchmark_mean:.2f}")
        print(f"Diferença  : {metric.difference_from_mean:+.2f}")
        print(f"Posição    : {metric.position_label}")

    print()
    print("MISSÃO")
    print("-" * 80)
    print(f"Título: {mission.title}")
    print(f"Partidas: {mission.games_target}")
    print(f"Objetivo: {mission.task.objective}")
    print(f"Hábito: {mission.task.habit}")
    print(f"Progresso: {mission.progress_bar}")

    print()
    print("CHECKLIST")
    print("-" * 80)

    for item in mission.task.checklist:
        print(f"□ {item}")

    print()
    print("COACH")
    print("-" * 80)
    print(report.coach_message)

    print()
    print("=" * 80)
    print(
        f"Tempo total: "
        f"{perf_counter() - start:.2f}s"
    )
    print("=" * 80)


if __name__ == "__main__":
    main()