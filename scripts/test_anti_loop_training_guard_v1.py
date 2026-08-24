from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.training.services.anti_loop_training_guard import (
    AntiLoopTrainingGuard,
)


def cycle(
    *,
    cycle_id: str,
    skill_id: str,
    result: str,
    evaluated_at: str,
):
    return {
        "cycle_id": cycle_id,
        "mission": {
            "task": {
                "id": f"task-{cycle_id}",
                "skill_id": skill_id,
                "title": f"Task {cycle_id}",
            }
        },
        "evaluation": {
            "result": result,
            "confidence": "MODERATE",
            "confidence_score": 69.99,
            "evaluated_at": evaluated_at,
        },
    }


def main() -> None:
    one_negative = AntiLoopTrainingGuard.evaluate(
        skill_id="leveling",
        training_history=[
            cycle(
                cycle_id="1",
                skill_id="leveling",
                result="NEGATIVE",
                evaluated_at="2026-08-01T10:00:00+00:00",
            )
        ],
    )

    improving = AntiLoopTrainingGuard.evaluate(
        skill_id="leveling",
        training_history=[
            cycle(
                cycle_id="2",
                skill_id="leveling",
                result="POSITIVE",
                evaluated_at="2026-08-10T10:00:00+00:00",
            ),
            cycle(
                cycle_id="1",
                skill_id="leveling",
                result="NEGATIVE",
                evaluated_at="2026-08-01T10:00:00+00:00",
            ),
        ],
    )

    two_negative = AntiLoopTrainingGuard.evaluate(
        skill_id="leveling",
        training_history=[
            cycle(
                cycle_id="2",
                skill_id="leveling",
                result="NEGATIVE",
                evaluated_at="2026-08-10T10:00:00+00:00",
            ),
            cycle(
                cycle_id="1",
                skill_id="leveling",
                result="NEGATIVE",
                evaluated_at="2026-08-01T10:00:00+00:00",
            ),
        ],
    )

    three_negative = AntiLoopTrainingGuard.evaluate(
        skill_id="leveling",
        training_history=[
            cycle(
                cycle_id="3",
                skill_id="leveling",
                result="NEGATIVE",
                evaluated_at="2026-08-15T10:00:00+00:00",
            ),
            cycle(
                cycle_id="2",
                skill_id="leveling",
                result="NEGATIVE",
                evaluated_at="2026-08-10T10:00:00+00:00",
            ),
            cycle(
                cycle_id="1",
                skill_id="leveling",
                result="NEGATIVE",
                evaluated_at="2026-08-01T10:00:00+00:00",
            ),
        ],
    )

    stable = AntiLoopTrainingGuard.evaluate(
        skill_id="consistency",
        training_history=[
            cycle(
                cycle_id="2",
                skill_id="consistency",
                result="STABLE",
                evaluated_at="2026-08-10T10:00:00+00:00",
            ),
            cycle(
                cycle_id="1",
                skill_id="consistency",
                result="STABLE",
                evaluated_at="2026-08-01T10:00:00+00:00",
            ),
        ],
    )

    two_inconclusive = AntiLoopTrainingGuard.evaluate(
        skill_id="consistency",
        training_history=[
            cycle(
                cycle_id="2",
                skill_id="consistency",
                result="INCONCLUSIVE",
                evaluated_at="2026-08-10T10:00:00+00:00",
            ),
            cycle(
                cycle_id="1",
                skill_id="consistency",
                result="INCONCLUSIVE",
                evaluated_at="2026-08-01T10:00:00+00:00",
            ),
        ],
    )

    non_consecutive = AntiLoopTrainingGuard.evaluate(
        skill_id="leveling",
        training_history=[
            cycle(
                cycle_id="l2",
                skill_id="leveling",
                result="NEGATIVE",
                evaluated_at="2026-08-12T10:00:00+00:00",
            ),
            cycle(
                cycle_id="c1",
                skill_id="consistency",
                result="POSITIVE",
                evaluated_at="2026-08-11T10:00:00+00:00",
            ),
            cycle(
                cycle_id="l1",
                skill_id="leveling",
                result="NEGATIVE",
                evaluated_at="2026-08-01T10:00:00+00:00",
            ),
        ],
    )

    checks = [
        (
            "1 NEGATIVE não bloqueia Skill",
            one_negative.action == "CONTINUE",
        ),
        (
            "1 ciclo mantém dificuldade",
            one_negative.task_progression == "HOLD",
        ),
        (
            "IMPROVING continua treino",
            improving.action == "CONTINUE",
        ),
        (
            "IMPROVING vira candidato a progressão",
            improving.task_progression
            == "ADVANCE_CANDIDATE",
        ),
        (
            "2 NEGATIVE pedem REASSESS",
            two_negative.action == "REASSESS",
        ),
        (
            "2 NEGATIVE pausam progressão",
            two_negative.task_progression
            == "PAUSE_AND_REASSESS",
        ),
        (
            "3 ciclos consecutivos regressivos aplicam COOLDOWN",
            three_negative.action
            == "COOLDOWN_SKILL",
        ),
        (
            "COOLDOWN exige streak 3",
            three_negative.consecutive_skill_cycles
            == 3,
        ),
        (
            "STABLE repetido rotaciona task",
            stable.action == "ROTATE_TASK"
            and stable.task_progression == "ROTATE",
        ),
        (
            "2 INCONCLUSIVE pedem REASSESS",
            two_inconclusive.action == "REASSESS",
        ),
        (
            "Ciclos separados por outra Skill não formam streak",
            non_consecutive.consecutive_skill_cycles
            == 1,
        ),
        (
            "Guard preserva tendência do Aggregator",
            improving.trend == "IMPROVING",
        ),
        (
            "Decisão possui cautela sobre prioridade",
            "não substitui" in one_negative.caution,
        ),
    ]

    print("=" * 82)
    print(
        "TFT INSIGHT - ANTI-LOOP TRAINING GUARD V1"
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
    print("CENÁRIO DE LOOP")
    print("-" * 82)
    print(
        f"Ação          : {three_negative.action}"
    )
    print(
        f"Progressão    : {three_negative.task_progression}"
    )
    print(
        f"Tendência     : {three_negative.trend}"
    )
    print(
        f"Streak        : {three_negative.consecutive_skill_cycles}"
    )
    print(
        f"Motivo        : {three_negative.rationale}"
    )

    print()
    print("=" * 82)
    print(
        f"PASSARAM: {passed}/{len(checks)}"
    )

    if passed == len(checks):
        print(
            "ANTI-LOOP TRAINING GUARD V1: VALIDADO"
        )
        raise SystemExit(0)

    print(
        "ANTI-LOOP TRAINING GUARD V1: AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
