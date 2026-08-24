from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.training.knowledge import get_tasks_for_skill
from src.training.models import TrainingTask
from src.training.services.task_difficulty_progression_engine import (
    TaskDifficultyProgressionEngine,
)


def main() -> None:
    leveling = {
        task.id: task
        for task in get_tasks_for_skill(
            "leveling"
        )
    }

    consistency = {
        task.id: task
        for task in get_tasks_for_skill(
            "consistency"
        )
    }

    advance_foundation = (
        TaskDifficultyProgressionEngine.decide(
            skill_id="leveling",
            current_task_id="plan_level_before_spending",
            progression_signal="ADVANCE_CANDIDATE",
        )
    )

    advance_intermediate = (
        TaskDifficultyProgressionEngine.decide(
            skill_id="leveling",
            current_task_id="balance_level_and_stability",
            progression_signal="ADVANCE_CANDIDATE",
        )
    )

    advance_advanced = (
        TaskDifficultyProgressionEngine.decide(
            skill_id="leveling",
            current_task_id="avoid_unplanned_rerolls",
            progression_signal="ADVANCE_CANDIDATE",
        )
    )

    rotate_advanced = (
        TaskDifficultyProgressionEngine.decide(
            skill_id="leveling",
            current_task_id="avoid_unplanned_rerolls",
            progression_signal="ROTATE",
        )
    )

    rotate_foundation = (
        TaskDifficultyProgressionEngine.decide(
            skill_id="leveling",
            current_task_id="plan_level_before_spending",
            progression_signal="ROTATE",
        )
    )

    reassess = (
        TaskDifficultyProgressionEngine.decide(
            skill_id="leveling",
            current_task_id="avoid_unplanned_rerolls",
            progression_signal="PAUSE_AND_REASSESS",
        )
    )

    hold = (
        TaskDifficultyProgressionEngine.decide(
            skill_id="leveling",
            current_task_id="balance_level_and_stability",
            progression_signal="HOLD",
        )
    )

    legacy = TrainingTask.from_dict(
        {
            "id": "legacy",
            "skill_id": "leveling",
            "title": "Legacy",
            "description": "Descrição",
            "objective": "Objetivo",
            "habit": "Hábito",
            "checklist": ["Item"],
            "success_signals": ["Sinal"],
        }
    )

    checks = [
        (
            "Leveling FOUNDATION correto",
            leveling["plan_level_before_spending"].difficulty
            == "FOUNDATION",
        ),
        (
            "Leveling INTERMEDIATE correto",
            leveling["balance_level_and_stability"].difficulty
            == "INTERMEDIATE",
        ),
        (
            "Leveling ADVANCED correto",
            leveling["avoid_unplanned_rerolls"].difficulty
            == "ADVANCED",
        ),
        (
            "Consistency FOUNDATION correto",
            consistency["define_simple_game_plan"].difficulty
            == "FOUNDATION",
        ),
        (
            "Consistency INTERMEDIATE correto",
            consistency["review_one_decision_per_match"].difficulty
            == "INTERMEDIATE",
        ),
        (
            "Consistency ADVANCED correto",
            consistency["reduce_unnecessary_risk"].difficulty
            == "ADVANCED",
        ),
        (
            "ADVANCE FOUNDATION -> INTERMEDIATE",
            advance_foundation.selected_task_id
            == "balance_level_and_stability"
            and advance_foundation.selected_difficulty
            == "INTERMEDIATE",
        ),
        (
            "ADVANCE INTERMEDIATE -> ADVANCED",
            advance_intermediate.selected_task_id
            == "avoid_unplanned_rerolls"
            and advance_intermediate.selected_difficulty
            == "ADVANCED",
        ),
        (
            "ADVANCE no teto mantém ADVANCED",
            advance_advanced.selected_task_id
            == "avoid_unplanned_rerolls",
        ),
        (
            "ROTATE em ADVANCED não aumenta dificuldade",
            rotate_advanced.selected_difficulty
            in {"INTERMEDIATE", "FOUNDATION"},
        ),
        (
            "ROTATE FOUNDATION sem alternativa segura mantém task",
            rotate_foundation.selected_task_id
            == "plan_level_before_spending",
        ),
        (
            "REASSESS volta para FOUNDATION",
            reassess.selected_task_id
            == "plan_level_before_spending",
        ),
        (
            "HOLD preserva task",
            hold.selected_task_id
            == "balance_level_and_stability",
        ),
        (
            "to_dict persiste difficulty",
            leveling[
                "balance_level_and_stability"
            ].to_dict()["difficulty"]
            == "INTERMEDIATE",
        ),
        (
            "from_dict legado continua compatível",
            legacy.difficulty == "FOUNDATION",
        ),
    ]

    print("=" * 82)
    print(
        "TFT INSIGHT - TASK DIFFICULTY + PROGRESSION ENGINE V1"
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
    print("PROGRESSÃO LEVELING")
    print("-" * 82)

    for task in get_tasks_for_skill(
        "leveling"
    ):
        print(
            f"{task.difficulty:12} | "
            f"{task.id} | {task.title}"
        )

    print()
    print("=" * 82)
    print(
        f"PASSARAM: {passed}/{len(checks)}"
    )

    if passed == len(checks):
        print(
            "TASK DIFFICULTY + PROGRESSION ENGINE V1: VALIDADO"
        )
        raise SystemExit(0)

    print(
        "TASK DIFFICULTY + PROGRESSION ENGINE V1: AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
