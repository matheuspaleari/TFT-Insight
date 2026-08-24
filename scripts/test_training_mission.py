from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.training import TrainingMission
from src.training.knowledge import get_tasks_for_skill


def main() -> None:
    tasks = get_tasks_for_skill(
        "leveling",
    )

    if not tasks:
        raise RuntimeError(
            "Nenhum exercício de Leveling foi encontrado."
        )

    task = tasks[0]

    mission = TrainingMission(
        task=task,
        games_target=5,
        games_completed=2,
        completed_match_ids=(
            "BR1_MATCH_001",
            "BR1_MATCH_002",
        ),
    )

    print()
    print("=" * 80)
    print("TFT INSIGHT - TRAINING MISSION")
    print("=" * 80)

    print(f"Mission ID       : {mission.mission_id}")
    print(f"Skill            : {mission.skill_id}")
    print(f"Título           : {mission.title}")
    print(f"Objetivo         : {mission.task.objective}")
    print(f"Hábito           : {mission.task.habit}")
    print(f"Progresso        : {mission.progress_bar}")
    print(
        f"Partidas         : "
        f"{mission.games_completed}/{mission.games_target}"
    )
    print(
        f"Percentual       : "
        f"{mission.progress_percentage:.1f}%"
    )
    print(
        f"Restantes        : "
        f"{mission.remaining_games}"
    )
    print(
        f"Concluída        : "
        f"{mission.is_completed}"
    )

    print()
    print("CHECKLIST")
    print("-" * 80)

    for item in mission.task.checklist:
        print(f"□ {item}")

    print()
    print("SINAIS DE SUCESSO")
    print("-" * 80)

    for signal in mission.task.success_signals:
        print(f"✓ {signal}")


if __name__ == "__main__":
    main()