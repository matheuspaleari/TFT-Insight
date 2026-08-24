from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.learning.services.habit_engine import HabitEngine


def context(
    *,
    matches=30,
    diversity=75.0,
    repetition=10.0,
    forces=False,
    usage=10.0,
):
    return {
        "contest": {
            "matches_analyzed": matches,
            "carry_contest_rate": 20.0,
            "high_contest_rate": 10.0,
            "placement_impact": 0.0,
            "placement_impact_label": "neutro",
            "confidence": 78.0,
        },
        "composition": {
            "matches_analyzed": matches,
            "diversity_rate": diversity,
            "repetition_rate": repetition,
            "forces_composition": forces,
            "most_used_usage_rate": usage,
        },
        "economy": {
            "matches_analyzed": matches,
            "label": "Regular",
            "level_8_rate": 60.0,
            "level_9_rate": 35.0,
            "average_gold_left": 12.0,
            "low_level_late_rate": 15.0,
            "confidence": 78.0,
        },
    }


SCENARIOS = [
    (
        "Flexibilidade estabelecida",
        context(
            diversity=75.0,
            repetition=12.0,
            forces=False,
            usage=12.0,
        ),
        ("composition_flexibility", "positive", "established"),
    ),
    (
        "Variedade observada",
        context(
            diversity=65.52,
            repetition=17.24,
            forces=False,
            usage=17.24,
        ),
        ("composition_variety", "positive", "observed"),
    ),
    (
        "Limite inferior da variedade",
        context(
            diversity=50.0,
            repetition=20.0,
            forces=False,
            usage=20.0,
        ),
        ("composition_variety", "positive", "observed"),
    ),
    (
        "Abaixo da variedade",
        context(
            diversity=49.99,
            repetition=20.0,
            forces=False,
            usage=20.0,
        ),
        None,
    ),
    (
        "Concentração por repetição",
        context(
            diversity=35.0,
            repetition=45.0,
            forces=False,
            usage=30.0,
        ),
        ("composition_concentration", "negative", "observed"),
    ),
    (
        "Concentração estabelecida",
        context(
            diversity=30.0,
            repetition=55.0,
            forces=True,
            usage=50.0,
        ),
        ("composition_concentration", "negative", "established"),
    ),
    (
        "Amostra pequena",
        context(
            matches=7,
            diversity=90.0,
            repetition=5.0,
        ),
        None,
    ),
]


def main():
    print("=" * 76)
    print("TFT INSIGHT - HABIT ENGINE V1.2 COMPOSITION VALIDATION")
    print("=" * 76)

    passed = 0

    for index, (name, payload, expected) in enumerate(SCENARIOS, 1):
        habits = HabitEngine.detect(
            coach_context=payload
        )

        composition_habit = next(
            (
                habit
                for habit in habits
                if habit.category == "composition"
            ),
            None,
        )

        actual = (
            (
                composition_habit.habit_id,
                composition_habit.direction,
                composition_habit.status,
            )
            if composition_habit
            else None
        )

        ok = actual == expected
        passed += int(ok)

        print()
        print(f"[{index}] {name}")
        print(f"Esperado: {expected}")
        print(f"Obtido  : {actual}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

    print()
    print("=" * 76)
    print(f"PASSARAM: {passed}/{len(SCENARIOS)}")

    if passed == len(SCENARIOS):
        print("HABIT ENGINE V1.2: VALIDADA")
        raise SystemExit(0)

    print("HABIT ENGINE V1.2: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
