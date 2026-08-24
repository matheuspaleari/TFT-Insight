from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.training.services.skill_training_history_aggregator import (
    SkillTrainingHistoryAggregator,
)


def cycle(
    *,
    cycle_id: str,
    skill_id: str,
    task_id: str,
    result: str | None,
    evaluated_at: str,
):
    data = {
        "cycle_id": cycle_id,
        "mission": {
            "task": {
                "id": task_id,
                "skill_id": skill_id,
                "title": task_id,
            }
        },
    }

    if result is not None:
        data["evaluation"] = {
            "result": result,
            "confidence": "MODERATE",
            "confidence_score": 69.99,
            "evaluated_at": evaluated_at,
        }

    return data


def main() -> None:
    one_cycle = SkillTrainingHistoryAggregator.aggregate(
        skill_id="leveling",
        training_history=[
            cycle(
                cycle_id="c1",
                skill_id="leveling",
                task_id="a",
                result="NEGATIVE",
                evaluated_at="2026-08-01T10:00:00+00:00",
            )
        ],
    )

    improving = SkillTrainingHistoryAggregator.aggregate(
        skill_id="leveling",
        training_history=[
            cycle(
                cycle_id="older",
                skill_id="leveling",
                task_id="a",
                result="NEGATIVE",
                evaluated_at="2026-08-01T10:00:00+00:00",
            ),
            cycle(
                cycle_id="newer",
                skill_id="leveling",
                task_id="b",
                result="POSITIVE",
                evaluated_at="2026-08-10T10:00:00+00:00",
            ),
        ],
    )

    regressing = SkillTrainingHistoryAggregator.aggregate(
        skill_id="leveling",
        training_history=[
            cycle(
                cycle_id="old-positive",
                skill_id="leveling",
                task_id="a",
                result="POSITIVE",
                evaluated_at="2026-08-01T10:00:00+00:00",
            ),
            cycle(
                cycle_id="new-negative",
                skill_id="leveling",
                task_id="b",
                result="NEGATIVE",
                evaluated_at="2026-08-10T10:00:00+00:00",
            ),
        ],
    )

    stable = SkillTrainingHistoryAggregator.aggregate(
        skill_id="consistency",
        training_history=[
            cycle(
                cycle_id="old-stable",
                skill_id="consistency",
                task_id="a",
                result="STABLE",
                evaluated_at="2026-08-01T10:00:00+00:00",
            ),
            cycle(
                cycle_id="new-stable",
                skill_id="consistency",
                task_id="b",
                result="STABLE",
                evaluated_at="2026-08-10T10:00:00+00:00",
            ),
        ],
    )

    mixed_with_inconclusive = SkillTrainingHistoryAggregator.aggregate(
        skill_id="leveling",
        training_history=[
            cycle(
                cycle_id="c1",
                skill_id="leveling",
                task_id="a",
                result="NEGATIVE",
                evaluated_at="2026-08-01T10:00:00+00:00",
            ),
            cycle(
                cycle_id="c2",
                skill_id="leveling",
                task_id="b",
                result="INCONCLUSIVE",
                evaluated_at="2026-08-05T10:00:00+00:00",
            ),
            cycle(
                cycle_id="c3",
                skill_id="leveling",
                task_id="c",
                result="POSITIVE",
                evaluated_at="2026-08-10T10:00:00+00:00",
            ),
        ],
    )

    all_skills = SkillTrainingHistoryAggregator.aggregate_all(
        training_history=[
            cycle(
                cycle_id="l1",
                skill_id="leveling",
                task_id="a",
                result="NEGATIVE",
                evaluated_at="2026-08-01T10:00:00+00:00",
            ),
            cycle(
                cycle_id="k1",
                skill_id="consistency",
                task_id="b",
                result="INCONCLUSIVE",
                evaluated_at="2026-08-02T10:00:00+00:00",
            ),
        ]
    )

    checks = [
        (
            "1 ciclo não inventa tendência",
            one_cycle.trend
            == "INSUFFICIENT_HISTORY",
        ),
        (
            "NEGATIVE -> POSITIVE é IMPROVING",
            improving.trend == "IMPROVING",
        ),
        (
            "Ordena por evaluated_at, não pela ordem recebida",
            improving.cycles[0].cycle_id
            == "newer",
        ),
        (
            "POSITIVE -> NEGATIVE é REGRESSING",
            regressing.trend == "REGRESSING",
        ),
        (
            "STABLE -> STABLE é STABLE",
            stable.trend == "STABLE",
        ),
        (
            "INCONCLUSIVE é contado",
            mixed_with_inconclusive.inconclusive_cycles
            == 1,
        ),
        (
            "INCONCLUSIVE não vira sinal conclusivo",
            mixed_with_inconclusive.conclusive_cycles
            == 2,
        ),
        (
            "Sinais conclusivos atravessam inconclusivo",
            mixed_with_inconclusive.trend
            == "IMPROVING",
        ),
        (
            "2 ciclos conclusivos têm confiança MODERATE",
            improving.trend_confidence
            == "MODERATE",
        ),
        (
            "Contagens POSITIVE corretas",
            improving.positive_cycles == 1,
        ),
        (
            "Contagens NEGATIVE corretas",
            improving.negative_cycles == 1,
        ),
        (
            "aggregate_all separa Skills",
            set(all_skills)
            == {"leveling", "consistency"},
        ),
        (
            "Modelo expõe rationale",
            bool(improving.rationale),
        ),
        (
            "Rationale não afirma causalidade",
            "não prova causalidade"
            in improving.rationale,
        ),
    ]

    print("=" * 82)
    print(
        "TFT INSIGHT - SKILL TRAINING HISTORY + TREND V1"
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
    print("EXEMPLO DE TENDÊNCIA")
    print("-" * 82)
    print(
        f"Skill       : {improving.skill_id}"
    )
    print(
        f"Ciclos      : {improving.cycles_total}"
    )
    print(
        f"Conclusivos : {improving.conclusive_cycles}"
    )
    print(
        f"Tendência   : {improving.trend}"
    )
    print(
        f"Confiança   : {improving.trend_confidence}"
    )
    print(
        f"Motivo      : {improving.rationale}"
    )

    print()
    print("=" * 82)
    print(
        f"PASSARAM: {passed}/{len(checks)}"
    )

    if passed == len(checks):
        print(
            "SKILL TRAINING HISTORY + TREND V1: VALIDADO"
        )
        raise SystemExit(0)

    print(
        "SKILL TRAINING HISTORY + TREND V1: AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
