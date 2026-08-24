from __future__ import annotations

import sys
from dataclasses import replace
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


def plan(skill_id: str, label: str, exercise_id: str) -> TrainingPlan:
    return TrainingPlan(
        primary_skill_id=skill_id,
        primary_skill_label=label,
        objective="objetivo",
        games_target=5,
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

    def load_training_mission(self, *, puuid):
        return self.mission

    def save_training_mission(self, *, puuid, mission):
        self.mission = mission
        return Path("fake/current.json")


def main() -> None:
    baseline = tuple(
        f"old-{i}"
        for i in range(30)
    )

    leveling = plan(
        "leveling",
        "Leveling",
        "leveling_timing_review",
    )

    consistency = plan(
        "consistency",
        "Consistência",
        "consistency_decision_checkpoint",
    )

    mission = MissionGenerator.generate_from_plan(
        training_plan=leveling,
        baseline_match_ids=baseline,
    )

    repo = FakeRepository(mission)
    service = PlayerTrainingService(
        player_repository=repo
    )

    one_new = (
        "new-1",
        *baseline[:29],
    )

    updated = service.sync_mission_progress(
        puuid="player",
        current_match_ids=one_new,
    )

    duplicate_run = service.sync_mission_progress(
        puuid="player",
        current_match_ids=one_new,
    )

    # Nova prioridade não interrompe 1/5.
    preserved = service.get_or_create_mission_from_plan(
        puuid="player",
        training_plan=consistency,
        baseline_match_ids=one_new,
    )

    five_new = (
        "new-5",
        "new-4",
        "new-3",
        "new-2",
        "new-1",
        *baseline[:25],
    )

    completed = service.sync_mission_progress(
        puuid="player",
        current_match_ids=five_new,
    )

    next_mission = service.get_or_create_mission_from_plan(
        puuid="player",
        training_plan=consistency,
        baseline_match_ids=five_new,
    )

    tests = [
        (
            "Baseline salvo ao criar missão",
            mission.baseline_match_ids == baseline,
        ),
        (
            "Uma partida nova conta 1/5",
            updated.games_completed == 1
            and updated.completed_match_ids == ("new-1",),
        ),
        (
            "Reexecução não duplica match_id",
            duplicate_run.games_completed == 1,
        ),
        (
            "Prioridade nova não interrompe ciclo ativo",
            preserved.mission_id == mission.mission_id
            and preserved.skill_id == "leveling",
        ),
        (
            "Cinco partidas concluem a missão",
            completed.is_completed
            and completed.games_completed == 5,
        ),
        (
            "Após conclusão nasce missão da prioridade atual",
            next_mission.mission_id != mission.mission_id
            and next_mission.skill_id == "consistency",
        ),
        (
            "Nova missão começa com baseline atual",
            next_mission.baseline_match_ids == five_new
            and next_mission.games_completed == 0,
        ),
    ]

    print("=" * 82)
    print("TFT INSIGHT - MISSION PROGRESS TRACKING V2 VALIDATION")
    print("=" * 82)

    passed = 0
    for index, (name, ok) in enumerate(tests, 1):
        passed += int(ok)
        print()
        print(f"[{index}] {name}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

    print()
    print("=" * 82)
    print(f"PASSARAM: {passed}/{len(tests)}")

    if passed == len(tests):
        print("MISSION PROGRESS TRACKING V2: VALIDADO")
        raise SystemExit(0)

    print("MISSION PROGRESS TRACKING V2: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
