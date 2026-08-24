from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.training.models import TrainingMission
from src.training.models.training_plan import (
    TrainingExercise,
    TrainingPlan,
)
from src.training.services.player_training_service import (
    PlayerTrainingService,
)


class FakeRepository:
    def __init__(
        self,
        *,
        current,
        history,
    ):
        self.current = current
        self.history = history
        self.saved = None
        self.archived = []

    def load_training_mission(self, *, puuid):
        return self.current

    def save_training_mission(self, *, puuid, mission):
        self.saved = mission
        self.current = mission
        return Path("fake/current.json")

    def archive_training_cycle(self, *, puuid, mission):
        self.archived.append(
            mission.mission_id
        )
        return Path(
            f"fake/history/{mission.mission_id}.json"
        )

    def list_training_cycles(self, *, puuid):
        return list(
            self.history
        )


def plan(
    *,
    skill_id: str,
    label: str,
) -> TrainingPlan:
    return TrainingPlan(
        primary_skill_id=skill_id,
        primary_skill_label=label,
        objective="Objetivo de teste",
        games_target=5,
        exercise=TrainingExercise(
            exercise_id="legacy-plan-exercise",
            title="Plano legado",
            instruction="Teste",
            checklist=("Teste",),
            success_signals=("Teste",),
            system_verification="Teste",
        ),
        secondary_focus=(),
        strengths_to_preserve=(),
        contexts_to_watch=(),
        rationale="Teste",
        confidence=90.0,
        limitations=(),
    )


def completed_consistency():
    task = PlayerTrainingService._select_task_by_id(
        skill_id="consistency",
        task_id="define_simple_game_plan",
    )

    return TrainingMission(
        task=task,
        games_target=5,
        games_completed=5,
        baseline_match_ids=tuple(
            f"old-{i}"
            for i in range(30)
        ),
        completed_match_ids=tuple(
            f"done-{i}"
            for i in range(5)
        ),
    )


def leveling_history():
    return [
        {
            "cycle_id": "old-leveling",
            "status": "completed",
            "mission": {
                "task": {
                    "id": "balance_level_and_stability",
                    "skill_id": "leveling",
                }
            },
            "evaluation": {
                "result": "NEGATIVE",
                "confidence": "MODERATE",
            },
        }
    ]


def main() -> None:
    completed = completed_consistency()

    repo = FakeRepository(
        current=completed,
        history=leveling_history(),
    )

    service = PlayerTrainingService(
        player_repository=repo
    )

    baseline = tuple(
        f"current-{i}"
        for i in range(30)
    )

    new_mission = (
        service.get_or_create_mission_from_plan(
            puuid="player",
            training_plan=plan(
                skill_id="leveling",
                label="Leveling",
            ),
            baseline_match_ids=baseline,
        )
    )

    checks = [
        (
            "Ciclo concluído é arquivado antes da troca",
            completed.mission_id
            in repo.archived,
        ),
        (
            "Nova Skill segue a prioridade atual",
            new_mission.skill_id
            == "leveling",
        ),
        (
            "Post-Cycle escolhe plan_level_before_spending",
            new_mission.task.id
            == "plan_level_before_spending",
        ),
        (
            "Não repete balance_level_and_stability",
            new_mission.task.id
            != "balance_level_and_stability",
        ),
        (
            "Nova missão começa em 0/5",
            new_mission.games_completed == 0
            and new_mission.games_target == 5,
        ),
        (
            "Nova missão não herda partidas concluídas",
            len(
                new_mission.completed_match_ids
            )
            == 0,
        ),
        (
            "Baseline novo é exatamente a janela atual",
            tuple(
                new_mission.baseline_match_ids
            )
            == baseline,
        ),
        (
            "Missão antiga e nova possuem IDs diferentes",
            new_mission.mission_id
            != completed.mission_id,
        ),
    ]

    # Segurança: missão ativa não pode ser interrompida.
    active_task = (
        PlayerTrainingService._select_task_by_id(
            skill_id="consistency",
            task_id="define_simple_game_plan",
        )
    )

    active = TrainingMission(
        task=active_task,
        games_target=5,
        games_completed=2,
        baseline_match_ids=baseline,
        completed_match_ids=(
            "m1",
            "m2",
        ),
    )

    active_repo = FakeRepository(
        current=active,
        history=leveling_history(),
    )

    active_service = PlayerTrainingService(
        player_repository=active_repo
    )

    preserved = (
        active_service.get_or_create_mission_from_plan(
            puuid="player",
            training_plan=plan(
                skill_id="leveling",
                label="Leveling",
            ),
            baseline_match_ids=baseline,
        )
    )

    checks.extend(
        [
            (
                "Missão ativa continua protegida",
                preserved.mission_id
                == active.mission_id,
            ),
            (
                "Missão ativa não é arquivada antecipadamente",
                len(active_repo.archived) == 0,
            ),
        ]
    )

    print("=" * 82)
    print(
        "TFT INSIGHT - POST-CYCLE MISSION INTEGRATION V1"
    )
    print("=" * 82)

    passed = 0

    for index, (name, ok) in enumerate(
        checks,
        start=1,
    ):
        passed += int(ok)
        print()
        print(f"[{index}] {name}")
        print(
            f"Status  : {'OK' if ok else 'ERRO'}"
        )

    print()
    print("-" * 82)
    print("TRANSIÇÃO ESPERADA")
    print("-" * 82)
    print(
        "Anterior    : consistency / "
        "define_simple_game_plan / 5/5"
    )
    print(
        "Prioridade  : leveling"
    )
    print(
        "Histórico   : balance_level_and_stability "
        "= NEGATIVE/MODERATE"
    )
    print(
        "Nova missão : "
        f"{new_mission.skill_id} / "
        f"{new_mission.task.id} / "
        f"{new_mission.games_completed}/"
        f"{new_mission.games_target}"
    )

    print()
    print("=" * 82)
    print(
        f"PASSARAM: {passed}/{len(checks)}"
    )

    if passed == len(checks):
        print(
            "POST-CYCLE MISSION INTEGRATION V1: VALIDADO"
        )
        raise SystemExit(0)

    print(
        "POST-CYCLE MISSION INTEGRATION V1: "
        "AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
