from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from src.learning.services.habit_engine import (
    HabitEngine,
)


def _context(
    *,
    matches: int = 30,
    carry_contest_rate: float = 20.0,
    high_contest_rate: float = 10.0,
    placement_impact: float | None = 0.0,
    placement_impact_label: str = "neutro",
    contest_confidence: float = 78.0,
    diversity_rate: float = 75.0,
    repetition_rate: float = 10.0,
    forces_composition: bool = False,
    most_used_usage_rate: float = 10.0,
    economy_label: str = "Muito forte",
    level_8_rate: float = 85.0,
    level_9_rate: float = 45.0,
    average_gold_left: float = 15.0,
    low_level_late_rate: float = 5.0,
    economy_confidence: float = 78.0,
) -> dict:
    return {
        "contest": {
            "matches_analyzed": matches,
            "carry_contest_rate": carry_contest_rate,
            "high_contest_rate": high_contest_rate,
            "placement_impact": placement_impact,
            "placement_impact_label": placement_impact_label,
            "confidence": contest_confidence,
        },
        "composition": {
            "matches_analyzed": matches,
            "diversity_rate": diversity_rate,
            "repetition_rate": repetition_rate,
            "forces_composition": forces_composition,
            "most_used_usage_rate": most_used_usage_rate,
        },
        "economy": {
            "matches_analyzed": matches,
            "label": economy_label,
            "level_8_rate": level_8_rate,
            "level_9_rate": level_9_rate,
            "average_gold_left": average_gold_left,
            "low_level_late_rate": low_level_late_rate,
            "confidence": economy_confidence,
        },
    }


SCENARIOS = [
    (
        "Carry contestado com impacto relevante",
        _context(
            carry_contest_rate=68.4,
            high_contest_rate=42.1,
            placement_impact=1.21,
            placement_impact_label="alto",
        ),
        {
            "recurring_carry_contest_exposure": (
                "negative",
                "established",
            ),
            "composition_flexibility": (
                "positive",
                "established",
            ),
            "consistent_level_progression": (
                "positive",
                "established",
            ),
        },
    ),
    (
        "Carry contestado sem piora observada",
        _context(
            carry_contest_rate=55.0,
            high_contest_rate=30.0,
            placement_impact=-0.20,
            placement_impact_label="neutro",
        ),
        {
            "recurring_carry_contest_exposure": (
                "neutral",
                "observed",
            ),
            "composition_flexibility": (
                "positive",
                "established",
            ),
            "consistent_level_progression": (
                "positive",
                "established",
            ),
        },
    ),
    (
        "Concentração de composição",
        _context(
            diversity_rate=35.0,
            repetition_rate=55.0,
            forces_composition=True,
            most_used_usage_rate=50.0,
        ),
        {
            "composition_concentration": (
                "negative",
                "established",
            ),
            "consistent_level_progression": (
                "positive",
                "established",
            ),
        },
    ),
    (
        "Recursos finais disponíveis",
        _context(
            economy_label="Regular",
            level_8_rate=65.0,
            level_9_rate=20.0,
            average_gold_left=31.0,
            low_level_late_rate=15.0,
        ),
        {
            "composition_flexibility": (
                "positive",
                "established",
            ),
            "resources_remaining_at_end": (
                "negative",
                "observed",
            ),
        },
    ),
    (
        "Progressão tardia limitada",
        _context(
            economy_label="Regular",
            level_8_rate=50.0,
            level_9_rate=20.0,
            average_gold_left=12.0,
            low_level_late_rate=35.0,
        ),
        {
            "composition_flexibility": (
                "positive",
                "established",
            ),
            "late_low_level_pattern": (
                "negative",
                "observed",
            ),
        },
    ),
    (
        "Amostra pequena não cria hábito",
        _context(
            matches=6,
            carry_contest_rate=90.0,
            diversity_rate=20.0,
            repetition_rate=80.0,
            forces_composition=True,
            economy_label="Fraco",
            low_level_late_rate=60.0,
        ),
        {},
    ),
]


def main() -> None:
    print("=" * 76)
    print("TFT INSIGHT - HABIT ENGINE V1 VALIDATION")
    print("=" * 76)

    passed = 0

    for index, (
        name,
        context,
        expected,
    ) in enumerate(
        SCENARIOS,
        start=1,
    ):
        habits = HabitEngine.detect(
            coach_context=context
        )

        actual = {
            habit.habit_id: (
                habit.direction,
                habit.status,
            )
            for habit in habits
        }

        ok = actual == expected

        print()
        print(f"[{index}] {name}")
        print(f"Esperado: {expected}")
        print(f"Obtido  : {actual}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

        for habit in habits:
            print(
                "  - "
                f"{habit.habit_id} | "
                f"{habit.direction} | "
                f"{habit.status} | "
                f"confiança {habit.confidence:.2f}%"
            )

        if ok:
            passed += 1

    print()
    print("=" * 76)
    print(f"PASSARAM: {passed}/{len(SCENARIOS)}")

    if passed == len(SCENARIOS):
        print("HABIT ENGINE V1: VALIDADA")
        raise SystemExit(0)

    print("HABIT ENGINE V1: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
