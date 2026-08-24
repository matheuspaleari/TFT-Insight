from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.training.models.training_plan import (
    TrainingExercise,
    TrainingPlan,
)
from src.training.services.mission_generator import MissionGenerator
from src.training.services.player_training_service import PlayerTrainingService


def make_plan(
    *,
    skill_id: str,
    skill_label: str,
    exercise_id: str,
    games_target: int = 5,
) -> TrainingPlan:
    return TrainingPlan(
        primary_skill_id=skill_id,
        primary_skill_label=skill_label,
        objective="objetivo",
        games_target=games_target,
        exercise=TrainingExercise(
            exercise_id=exercise_id,
            title="exercício",
            instruction="instrução",
            checklist=("item",),
            success_signals=("sinal",),
            system_verification="parcial",
        ),
        secondary_focus=(),
        strengths_to_preserve=(),
        contexts_to_watch=(),
        rationale="motivo",
        confidence=90.0,
        limitations=(),
    )


class FakeRepository:
    def __init__(self, mission=None):
        self.mission = mission
        self.saved = []

    def load_training_mission(self, *, puuid):
        return self.mission

    def save_training_mission(self, *, puuid, mission):
        self.mission = mission
        self.saved.append((puuid, mission))
        return Path("fake") / "training_mission.json"


def main() -> None:
    leveling_plan = make_plan(
        skill_id="leveling",
        skill_label="Leveling",
        exercise_id="leveling_timing_review",
    )

    consistency_plan = make_plan(
        skill_id="consistency",
        skill_label="Consistência",
        exercise_id="consistency_decision_checkpoint",
    )

    leveling_mission = MissionGenerator.generate_from_plan(
        training_plan=leveling_plan
    )

    consistency_mission = MissionGenerator.generate_from_plan(
        training_plan=consistency_plan
    )

    repo = FakeRepository(
        mission=leveling_mission
    )

    service = PlayerTrainingService(
        player_repository=repo
    )

    reused = service.get_or_create_mission_from_plan(
        puuid="player",
        training_plan=leveling_plan,
    )

    changed = service.get_or_create_mission_from_plan(
        puuid="player",
        training_plan=consistency_plan,
    )

    tests = [
        (
            "Leveling seleciona exercício coerente",
            leveling_mission.task.id
            == "balance_level_and_stability",
        ),
        (
            "Consistência seleciona plano simples",
            consistency_mission.task.id
            == "define_simple_game_plan",
        ),
        (
            "games_target vem do TrainingPlan",
            leveling_mission.games_target == 5,
        ),
        (
            "Missão ativa da mesma Skill é reutilizada",
            reused.mission_id == leveling_mission.mission_id
            and len(repo.saved) == 1,
        ),
        (
            "Mudança de Skill cria nova missão",
            changed.skill_id == "consistency"
            and changed.mission_id != leveling_mission.mission_id,
        ),
        (
            "TrainingMission continua controlando progresso",
            changed.games_completed == 0
            and changed.progress_percentage == 0.0
            and changed.remaining_games == 5,
        ),
    ]

    print("=" * 82)
    print("TFT INSIGHT - TRAINING PLAN -> MISSION INTEGRATION V1")
    print("=" * 82)

    passed = 0

    for index, (name, ok) in enumerate(
        tests,
        start=1,
    ):
        passed += int(ok)

        print()
        print(f"[{index}] {name}")
        print(
            f"Status  : {'OK' if ok else 'ERRO'}"
        )

    print()
    print("=" * 82)
    print(
        f"PASSARAM: {passed}/{len(tests)}"
    )

    if passed == len(tests):
        print(
            "TRAINING PLAN -> MISSION INTEGRATION V1: VALIDADA"
        )
        raise SystemExit(0)

    print(
        "TRAINING PLAN -> MISSION INTEGRATION V1: AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
