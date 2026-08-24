from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.training.services.post_cycle_decision_engine import (
    PostCycleDecisionEngine,
)


def cycle(
    skill_id: str,
    task_id: str,
    result: str,
    confidence: str = "MODERATE",
):
    return {
        "cycle_id": f"{skill_id}-{task_id}",
        "mission": {
            "task": {
                "skill_id": skill_id,
                "id": task_id,
            }
        },
        "evaluation": {
            "result": result,
            "confidence": confidence,
        },
    }


def mission(
    skill_id: str,
    task_id: str,
):
    return {
        "task": {
            "skill_id": skill_id,
            "id": task_id,
        }
    }


def main() -> None:
    # Cenário real atual:
    # missão concluída = consistency
    # prioridade nova = leveling
    # histórico leveling = NEGATIVE no balance_level_and_stability
    real = PostCycleDecisionEngine.decide(
        priority_skill_id="leveling",
        completed_mission=mission(
            "consistency",
            "define_simple_game_plan",
        ),
        training_history=[
            cycle(
                "leveling",
                "balance_level_and_stability",
                "NEGATIVE",
            )
        ],
    )

    same_negative = PostCycleDecisionEngine.decide(
        priority_skill_id="leveling",
        completed_mission=mission(
            "leveling",
            "balance_level_and_stability",
        ),
        training_history=[
            cycle(
                "leveling",
                "balance_level_and_stability",
                "NEGATIVE",
            )
        ],
    )

    inconclusive = PostCycleDecisionEngine.decide(
        priority_skill_id="consistency",
        completed_mission=mission(
            "consistency",
            "review_one_decision_per_match",
        ),
        training_history=[
            cycle(
                "consistency",
                "review_one_decision_per_match",
                "INCONCLUSIVE",
                "LOW",
            )
        ],
    )

    positive = PostCycleDecisionEngine.decide(
        priority_skill_id="leveling",
        completed_mission=mission(
            "leveling",
            "plan_level_before_spending",
        ),
        training_history=[
            cycle(
                "leveling",
                "plan_level_before_spending",
                "POSITIVE",
            )
        ],
    )

    checks = [
        (
            "Cenário real muda Consistency -> Leveling",
            real.action == "CHANGE_PRIORITY",
        ),
        (
            "Histórico NEGATIVE de Leveling é usado",
            real.previous_result == "NEGATIVE"
            and real.history_used,
        ),
        (
            "Prioridade Leveling não é bloqueada pelo NEGATIVE",
            real.target_skill_id == "leveling",
        ),
        (
            "Não repete balance_level_and_stability imediatamente",
            real.suggested_task_id
            != "balance_level_and_stability",
        ),
        (
            "Primeiro exercício Leveling ainda não usado é sugerido",
            real.suggested_task_id
            == "plan_level_before_spending",
        ),
        (
            "Mesma Skill NEGATIVE gera REPEAT_SKILL",
            same_negative.action == "REPEAT_SKILL",
        ),
        (
            "INCONCLUSIVE repete o mesmo exercício",
            inconclusive.action == "RETRY_TASK"
            and inconclusive.task_strategy
            == "RETRY_SAME_TASK"
            and inconclusive.suggested_task_id
            == "review_one_decision_per_match",
        ),
        (
            "POSITIVE permite avançar dentro da Skill",
            positive.action == "ADVANCE_SKILL",
        ),
        (
            "POSITIVE rotaciona para exercício ainda não usado",
            positive.suggested_task_id
            == "balance_level_and_stability",
        ),
    ]

    print("=" * 82)
    print("TFT INSIGHT - POST-CYCLE DECISION ENGINE V1")
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
    print("CENÁRIO REAL ATUAL")
    print("-" * 82)
    print(f"Ação             : {real.action}")
    print(f"Skill-alvo       : {real.target_skill_id}")
    print(f"Skill concluída  : {real.previous_skill_id}")
    print(f"Histórico-alvo   : {real.previous_result}")
    print(f"Estratégia task  : {real.task_strategy}")
    print(f"Task anterior    : {real.previous_task_id}")
    print(f"Task sugerida    : {real.suggested_task_id}")
    print(f"Motivo           : {real.rationale}")

    print()
    print("=" * 82)
    print(
        f"PASSARAM: {passed}/{len(checks)}"
    )

    if passed == len(checks):
        print(
            "POST-CYCLE DECISION ENGINE V1: VALIDADO"
        )
        raise SystemExit(0)

    print(
        "POST-CYCLE DECISION ENGINE V1: AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
